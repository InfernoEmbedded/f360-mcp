import adsk.core
import adsk.fusion
import traceback
import threading
import socket
import json
import time
import os
import sys
import collections
from datetime import datetime

from .commands import (
    registry, sketch, solid, construction, assembly, params, data, query, materials, utils, internal
)
from .commands.base import get_active_design, _get_timeline_health_map, _group_stack

# Globals
app = None
ui  = None
server_thread = None
stop_event = threading.Event()
handlers = []

# Persistent Settings
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.json')
DEFAULT_SETTINGS = {
    'port': 30011,
    'interface': '127.0.0.1'
}

# Log Buffer
log_buffer = collections.deque(maxlen=100)

def add_to_log(message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    entry = f"[{timestamp}] {message}"
    log_buffer.append(entry)
    if app:
        app.log(entry)

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
    except:
        pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except:
        app.log("Failed to save settings.")

# UI Commands
class SettingsCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            settings = load_settings()
            
            inputs = cmd.commandInputs
            inputs.addIntegerSliderCommandInput('port', 'TCP Port', 1024, 65535, False)
            inputs.itemById('port').valueOne = settings.get('port', 30011)
            
            interface_input = inputs.addDropDownCommandInput('interface', 'Interface', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            interface_input.listItems.add('Local (127.0.0.1)', settings.get('interface') == '127.0.0.1', '')
            interface_input.listItems.add('All (0.0.0.0)', settings.get('interface') == '0.0.0.0', '')
            
            on_execute = SettingsCommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
        except:
            ui_local = adsk.core.Application.get().userInterface
            if ui_local:
                ui_local.messageBox('Failed to create settings dialog:\n{}'.format(traceback.format_exc()))

class SettingsCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            
            new_port = inputs.itemById('port').valueOne
            new_interface = '127.0.0.1' if 'Local' in inputs.itemById('interface').selectedItem.name else '0.0.0.0'
            
            settings = load_settings()
            if settings['port'] != new_port or settings['interface'] != new_interface:
                save_settings({'port': new_port, 'interface': new_interface})
                ui.messageBox('Settings saved. Please stop and start the Add-in to apply changes.')
        except:
            ui_local = adsk.core.Application.get().userInterface
            if ui_local:
                ui_local.messageBox('Failed to save settings:\n{}'.format(traceback.format_exc()))

# Log Viewer Commands
class LogCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            inputs = cmd.commandInputs
            
            txt_box = inputs.addTextBoxCommandInput('log_text', 'MCP Server Log', '', 20, True)
            txt_box.isFullWidth = True
            
            # Populate log
            content = "\n".join(list(log_buffer))
            if not content:
                content = "No logs yet."
            txt_box.formattedText = f"<pre>{content}</pre>"
        except:
            ui_local = adsk.core.Application.get().userInterface
            if ui_local:
                ui_local.messageBox('Failed to create log dialog:\n{}'.format(traceback.format_exc()))

def handle_client(conn, addr):
    add_to_log(f'Connected by {addr}')
    try:
        while not stop_event.is_set():
            try:
                data = conn.recv(16384)
                if not data:
                    break
                
                message = data.decode('utf-8').strip()
                if not message:
                    continue
                    
                request = json.loads(message)
                method = request.get('method')
                params = request.get('params', {})
                request_id = request.get('id')
                
                # Log the request
                try:
                    p_str = json.dumps(params)
                except:
                    p_str = str(params)
                params_str = p_str[:100] + ('...' if len(p_str) > 100 else '')
                add_to_log(f"REQ [{method}] {params_str}")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                }
                
                try:
                    dispatch = registry.dispatch_table
                    if method in dispatch:
                        # Capture state before
                        old_issues = _get_timeline_health_map(app)
                        design = get_active_design(app)
                        pre_count = design.timeline.count
                        
                        result = dispatch[method](app, **params)
                        
                        # Capture state after
                        new_issues_map = _get_timeline_health_map(app)
                        post_count = design.timeline.count

                        # Automatic grouping if no manual group is active
                        if post_count > pre_count and not _group_stack:
                            from .commands.base import _is_internal_command
                            if not _is_internal_command(method):
                                try:
                                    group_name = f"Group: {method}"
                                    group = design.timeline.timelineGroups.add(pre_count, post_count - 1)
                                    group.name = group_name
                                except Exception as e:
                                    add_to_log(f"Auto-grouping failed: {str(e)}")
                        
                        # Compare health
                        introduced = []
                        for idx, data in new_issues_map.items():
                            if idx not in old_issues or old_issues[idx] != data:
                                name = "Unnamed"
                                try:
                                    name = design.timeline.item(idx).entity.name
                                except: pass
                                introduced.append({
                                    "index": idx,
                                    "name": name,
                                    "type": data[0],
                                    "health": data[1],
                                    "message": data[2]
                                })
                        
                        if isinstance(result, dict):
                            result["new_issues"] = introduced
                        else:
                            result = {"result": result, "new_issues": introduced}
                            
                        response['result'] = result
                    else:
                        response['error'] = {"code": -32601, "message": f"Method not found: {method}"}
                except Exception as e:
                    response['error'] = {"code": -32000, "message": str(e)}
                    add_to_log(f"Error executing command: {traceback.format_exc()}")
                
                # Send response
                conn.sendall(json.dumps(response).encode('utf-8') + b'\n')
                
                # Log failure if any
                if "error" in response:
                    err = response.get("error", {})
                    if isinstance(err, dict):
                        msg = err.get("message", "Unknown error")
                        add_to_log(f"ERR [{method}] {msg}")

            except socket.timeout:
                continue
            except json.JSONDecodeError:
                conn.sendall(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}).encode('utf-8') + b'\n')
    except Exception as e:
        add_to_log(f'Error handling client: {traceback.format_exc()}')
    finally:
        conn.close()
        add_to_log(f'Disconnected from {addr}')

def server_loop():
    try:
        settings = load_settings()
        port = settings.get('port', 30011)
        interface = settings.get('interface', '127.0.0.1')
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((interface, port))
            s.listen()
            s.settimeout(1.0)
            add_to_log(f"MCP Add-In TCP Server listening on {interface}:{port}")
            
            while not stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    add_to_log(f"Accept error: {str(e)}")
    except Exception as e:
        if app:
            add_to_log(f"Server loop error: {traceback.format_exc()}")

def run(context):
    global app, ui, server_thread, stop_event
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # 1. Start Server
        stop_event.clear()
        server_thread = threading.Thread(target=server_loop)
        server_thread.daemon = True 
        server_thread.start()
        
        # 2. Setup UI
        cmd_defs = ui.commandDefinitions
        
        # --- Settings Command ---
        settings_cmd = cmd_defs.itemById('mcp_settings_cmd')
        if settings_cmd:
            settings_cmd.deleteMe()
            
        settings_cmd = cmd_defs.addButtonDefinition(
            'mcp_settings_cmd', 
            'MCP Settings', 
            'Configure the Model Context Protocol server.',
            './resources'
        )
        
        on_settings_created = SettingsCommandCreatedHandler()
        settings_cmd.commandCreated.add(on_settings_created)
        handlers.append(on_settings_created)
        
        # --- Log Command ---
        log_view_cmd = cmd_defs.itemById('mcp_log_view_cmd')
        if log_view_cmd:
            log_view_cmd.deleteMe()
            
        log_view_cmd = cmd_defs.addButtonDefinition(
            'mcp_log_view_cmd', 
            'View MCP Log', 
            'View the recent MCP server activity log.',
            './resources' # Using same icon for now
        )
        
        on_log_created = LogCommandCreatedHandler()
        log_view_cmd.commandCreated.add(on_log_created)
        handlers.append(on_log_created)
        
        # Add to Utility Panel
        utility_panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        if utility_panel:
            # Add Settings
            if not utility_panel.controls.itemById('mcp_settings_cmd'):
                utility_panel.controls.addCommand(settings_cmd)
            # Add Log View
            if not utility_panel.controls.itemById('mcp_log_view_cmd'):
                utility_panel.controls.addCommand(log_view_cmd)
        
        settings = load_settings()
        add_to_log(f"MCP Add-In Started. Listening on {settings['interface']}:{settings['port']}")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    global handlers
    try:
        add_to_log('Stopping MCP Add-In...')
        stop_event.set()
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=2.0)
            
        # UI Cleanup
        cmd_defs = ui.commandDefinitions
        for cid in ['mcp_settings_cmd', 'mcp_log_view_cmd']:
            cmd = cmd_defs.itemById(cid)
            if cmd:
                cmd.deleteMe()
            
        utility_panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        if utility_panel:
            for cid in ['mcp_settings_cmd', 'mcp_log_view_cmd']:
                control = utility_panel.controls.itemById(cid)
                if control:
                    control.deleteMe()
        
        handlers = []
        app.log('MCP Add-In Stopped.')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
