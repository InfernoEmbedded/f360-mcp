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

# Log Buffer & File
LOG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'f360_mcp.log')
log_buffer = collections.deque(maxlen=100)

def add_to_log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{timestamp}] {message}"
    log_buffer.append(entry)
    
    # Persistent File Logging
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(entry + '\n')
    except:
        pass

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
        add_to_log("Failed to save settings.")

# --- Thread Synchronization for Main Thread Execution ---
pending_requests = {}
request_id_counter = 0
request_lock = threading.Lock()
mcp_custom_event_id = 'FusionMCP_CustomEvent'
mcp_custom_event = None

class PendingRequest:
    def __init__(self, method, params):
        self.method = method
        self.params = params
        self.event = threading.Event()
        self.result = None
        self.error = None

class MCPCustomEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            event_data = json.loads(args.additionalInfo)
            req_id = event_data.get("id")
            method = event_data.get("method")
            params = event_data.get("params")
            
            with request_lock:
                req = pending_requests.get(req_id)
            if not req: return

            try:
                dispatch = registry.dispatch_table
                if method in dispatch:
                    # Capture state before
                    old_issues = _get_timeline_health_map(app)
                    design = get_active_design(app)
                    pre_count = design.timeline.count if design else 0
                    
                    # Execute
                    result = dispatch[method](app, **params)
                    
                    # Capture state after
                    new_issues_map = _get_timeline_health_map(app)
                    post_count = design.timeline.count if design else 0

                    # Automatic grouping
                    if design and post_count > pre_count and not _group_stack:
                        from .commands.base import _is_internal_command
                        if not _is_internal_command(method):
                            try:
                                group_name = f"Group: {method}"
                                # Fusion timeline is 0-indexed for items, but add takes start, end
                                group = design.timeline.timelineGroups.add(pre_count, post_count - 1)
                                group.name = group_name
                            except Exception as e:
                                add_to_log(f"Auto-grouping failed: {str(e)}")
                    
                    # Compare health
                    if not method.startswith('_') and design:
                        introduced = []
                        for idx, data in new_issues_map.items():
                            if idx not in old_issues or old_issues[idx] != data:
                                name = "Unnamed"
                                try: name = design.timeline.item(idx).entity.name
                                except: pass
                                introduced.append({
                                    "index": idx, "name": name, "type": data[0], "health": data[1], "message": data[2]
                                })
                        
                        if isinstance(result, dict):
                            result["new_issues"] = introduced
                        else:
                            result = {"result": result, "new_issues": introduced}
                    
                    req.result = result
                else:
                    req.error = {"code": -32601, "message": f"Method not found: {method}"}
            except Exception as e:
                req.error = {"code": -32000, "message": str(e)}
                add_to_log(f"Error executing command {method}: {traceback.format_exc()}")
            finally:
                req.event.set()
        except:
            add_to_log(f"Custom event critical error: {traceback.format_exc()}")

def dispatch_to_main_thread(method, params):
    global request_id_counter
    with request_lock:
        request_id_counter += 1
        req_id = request_id_counter
        req = PendingRequest(method, params)
        pending_requests[req_id] = req
    
    if mcp_custom_event:
        mcp_custom_event.fire(json.dumps({"id": req_id, "method": method, "params": params}))
    else:
        with request_lock: del pending_requests[req_id]
        raise Exception("MCP Custom Event not registered")
        
    if req.event.wait(60.0):
        with request_lock: del pending_requests[req_id]
        if req.error:
            # req.error is already a dict with code/message
            raise Exception(json.dumps(req.error))
        return req.result
    else:
        with request_lock:
            if req_id in pending_requests: del pending_requests[req_id]
        raise Exception("Timeout waiting for Fusion 360 main thread response")

# --- UI Handlers ---
class SettingsCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            settings = load_settings()
            inputs = cmd.commandInputs
            inputs.addIntegerSpinnerCommandInput('port', 'TCP Port', 1024, 65535, 1, settings.get('port', 30011))
            interface_input = inputs.addDropDownCommandInput('interface', 'Interface', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            interface_input.listItems.add('Local (127.0.0.1)', settings.get('interface') == '127.0.0.1', '')
            interface_input.listItems.add('All (0.0.0.0)', settings.get('interface') == '0.0.0.0', '')
            on_execute = SettingsCommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
        except: add_to_log(f'Failed to create settings dialog: {traceback.format_exc()}')

class SettingsCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            new_port = inputs.itemById('port').valueOne
            new_interface = '127.0.0.1' if 'Local' in inputs.itemById('interface').selectedItem.name else '0.0.0.0'
            save_settings({'port': new_port, 'interface': new_interface})
            add_to_log('Settings saved. Please stop and start the Add-in to apply changes.')
        except: add_to_log(f'Failed to save settings: {traceback.format_exc()}')

class LogCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            # Re-read file logs for the viewer
            display_logs = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    display_logs = f.readlines()[-100:]
            content = "".join(display_logs) if display_logs else "No logs yet."
            txt_box = cmd.commandInputs.addTextBoxCommandInput('log_text', 'MCP Server Log', content, 20, True)
            txt_box.isFullWidth = True
        except: add_to_log(f'Failed to create log dialog: {traceback.format_exc()}')

# --- Server Logic ---
def handle_client(conn, addr):
    add_to_log(f'Connected by {addr}')
    try:
        while not stop_event.is_set():
            try:
                data = conn.recv(16384)
                if not data: break
                
                message = data.decode('utf-8').strip()
                if not message: continue
                
                request = json.loads(message)
                method = request.get('method')
                params = request.get('params', {})
                request_id = request.get('id')
                
                add_to_log(f"REQ [{method}]")
                
                response = {"jsonrpc": "2.0", "id": request_id}
                
                try:
                    # Dispatch to main thread
                    result = dispatch_to_main_thread(method, params)
                    response['result'] = result
                except Exception as e:
                    # e might be a JSON-encoded error dict
                    try:
                        err_data = json.loads(str(e))
                        response['error'] = err_data
                    except:
                        response['error'] = {"code": -32000, "message": str(e)}
                    add_to_log(f"Command execution error: {str(e)}")
                
                conn.sendall(json.dumps(response).encode('utf-8') + b'\n')
                if "error" in response:
                    add_to_log(f"ERR [{method}] {response['error'].get('message')}")

            except socket.timeout: continue
            except json.JSONDecodeError:
                conn.sendall(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}).encode('utf-8') + b'\n')
    except: add_to_log(f'Client handler error: {traceback.format_exc()}')
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
            add_to_log(f"MCP TCP Server listening on {interface}:{port}")
            while not stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                    t.start()
                except socket.timeout: continue
                except: add_to_log(f"Accept error: {traceback.format_exc()}")
    except: add_to_log(f"Server loop fatal: {traceback.format_exc()}")

def run(context):
    global app, ui, server_thread, stop_event, mcp_custom_event
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # 0. Register Custom Event
        mcp_custom_event = ui.registerCustomEvent(mcp_custom_event_id)
        on_mcp_event = MCPCustomEventHandler()
        mcp_custom_event.add(on_mcp_event)
        handlers.append(on_mcp_event)

        # 1. Start Server
        stop_event.clear()
        server_thread = threading.Thread(target=server_loop)
        server_thread.start()
        
        # 2. Setup UI
        cmd_defs = ui.commandDefinitions
        for cid in ['mcp_settings_cmd', 'mcp_log_view_cmd']:
            old = cmd_defs.itemById(cid)
            if old: old.deleteMe()
            
        settings_cmd = cmd_defs.addButtonDefinition('mcp_settings_cmd', 'MCP Settings', 'Configure MCP server.', './resources')
        on_settings = SettingsCommandCreatedHandler()
        settings_cmd.commandCreated.add(on_settings)
        handlers.append(on_settings)
        
        log_cmd = cmd_defs.addButtonDefinition('mcp_log_view_cmd', 'View MCP Log', 'View activity log.', './resources')
        on_log = LogCommandCreatedHandler()
        log_cmd.commandCreated.add(on_log)
        handlers.append(on_log)
        
        panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        if panel:
            if not panel.controls.itemById('mcp_settings_cmd'): panel.controls.addCommand(settings_cmd)
            if not panel.controls.itemById('mcp_log_view_cmd'): panel.controls.addCommand(log_cmd)
        
        add_to_log("MCP Add-In Version 1.1 (Stability Patch) Started.")
    except: add_to_log(f'Failed to start Add-in: {traceback.format_exc()}')

def stop(context):
    global handlers, mcp_custom_event
    try:
        add_to_log('Stopping MCP Add-In...')
        stop_event.set()
        if server_thread: server_thread.join(timeout=2.0)
        
        if mcp_custom_event:
            mcp_custom_event.unregisterCustomEvent()
            mcp_custom_event = None

        cmd_defs = ui.commandDefinitions
        for cid in ['mcp_settings_cmd', 'mcp_log_view_cmd']:
            cmd = cmd_defs.itemById(cid)
            if cmd: cmd.deleteMe()
            
        panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        if panel:
            for cid in ['mcp_settings_cmd', 'mcp_log_view_cmd']:
                ctrl = panel.controls.itemById(cid)
                if ctrl: ctrl.deleteMe()
        
        handlers = []
        app.log('MCP Add-In Stopped.')
    except: add_to_log(f'Failed to stop Add-in: {traceback.format_exc()}')
