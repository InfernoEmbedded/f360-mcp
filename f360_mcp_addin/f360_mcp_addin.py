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
from typing import Any

from .commands import (
    registry, command, sketch, solid, construction, assembly, params, data, query, materials, utils, internal
)
from .commands.base import get_active_design, _get_timeline_health_map, _group_stack

# Globals
VERSION = "1.9"
app: Any | None = None
ui: Any | None = None
server_thread: threading.Thread | None = None
stop_event = threading.Event()
handlers = []

# Persistent Settings & Files
ADDIN_PATH = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE = os.path.join(ADDIN_PATH, 'settings.json')
LOG_FILE = os.path.join(ADDIN_PATH, 'f360_mcp.log')
RESOURCES_PATH = os.path.join(ADDIN_PATH, 'resources')

DEFAULT_SETTINGS = {
    'port': 30011,
    'interface': '127.0.0.1'
}

# Log Buffer
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

    # Fallback to Fusion's own log (visible in Text Commands)
    try:
        if app: app.log(entry)
    except: pass

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
    except: pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except: add_to_log("Failed to save settings.")

# --- Thread Synchronization ---
pending_requests = {}
request_id_counter = 0
request_lock = threading.Lock()
mcp_custom_event_id = 'FusionMCP_CustomEvent'
mcp_custom_event: Any | None = None

class PendingRequest:
    def __init__(self, method, params):
        self.method = method
        self.params = params
        self.event = threading.Event()
        self.result = None
        self.error = None

class MCPCustomEventHandler(adsk.core.CustomEventHandler):
    def __init__(self): super().__init__()
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
                    old_issues = _get_timeline_health_map(app)
                    design = get_active_design(app)
                    pre_count = design.timeline.count if design else 0
                    
                    result = dispatch[method](app, **params)
                    
                    new_issues_map = _get_timeline_health_map(app)
                    post_count = design.timeline.count if design else 0

                    if design and post_count > pre_count and not _group_stack:
                        from .commands.base import _is_internal_command
                        if not _is_internal_command(method):
                            try:
                                group = design.timeline.timelineGroups.add(pre_count, post_count - 1)
                                group.name = f"Group: {method}"
                            except Exception as e: add_to_log(f"Auto-grouping failed: {str(e)}")
                    
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
                        if isinstance(result, dict): result["new_issues"] = introduced
                        else: result = {"result": result, "new_issues": introduced}
                    req.result = result
                else:
                    req.error = {"code": -32601, "message": f"Method not found: {method}"}
            except Exception as e:
                req.error = {"code": -32000, "message": str(e)}
                add_to_log(f"Error executing command {method}: {traceback.format_exc()}")
            finally:
                req.event.set()
        except: add_to_log(f"Custom event critical error: {traceback.format_exc()}")

def dispatch_to_main_thread(method, params):
    global request_id_counter
    with request_lock:
        request_id_counter += 1
        req_id = request_id_counter
        req = PendingRequest(method, params)
        pending_requests[req_id] = req
    
    if mcp_custom_event and app is not None:
        app.fireCustomEvent(mcp_custom_event_id, json.dumps({"id": req_id, "method": method, "params": params}))
    else:
        with request_lock: del pending_requests[req_id]
        raise Exception("MCP Custom Event not registered")
        
    if req.event.wait(60.0):
        with request_lock:
            if req_id in pending_requests: del pending_requests[req_id]
        if req.error: raise Exception(json.dumps(req.error))
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
            display_logs = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    display_logs = f.readlines()[-100:]
            content = "".join(display_logs) if display_logs else "No logs yet."
            txt_box = cmd.commandInputs.addTextBoxCommandInput('log_text', 'MCP Server Log', content, 20, True)
            txt_box.isFullWidth = True
        except: add_to_log(f'Failed to create log dialog: {traceback.format_exc()}')

@command(name="get_version")
def get_version_info(app):
    return VERSION

def is_background_safe(method):
    # These tools don't touch the Fusion API or are safe to read from file/memory
    # reload_addin is safe because it creates a temp file and fires a text command
    return method in ['get_addin_logs', '_get_command_metadata', 'get_version', 'reload_addin', 'get_system_info']

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
                    if is_background_safe(method):
                        # Execute directly in the background thread
                        dispatch = registry.dispatch_table
                        if method == 'get_version':
                            result = get_version_info(None)
                            response['result'] = result
                        elif method in dispatch:
                            # Pass None as app, these tools don't use it
                            result = dispatch[method](None, **params)
                            response['result'] = result
                        else:
                            response['error'] = {"code": -32601, "message": f"Method not found: {method}"}
                    else:
                        # Dispatch to main thread
                        result = dispatch_to_main_thread(method, params)
                        response['result'] = result
                except Exception as e:
                    try: response['error'] = json.loads(str(e))
                    except: response['error'] = {"code": -32000, "message": str(e)}
                    add_to_log(f"Command execution error: {str(e)}")
                conn.sendall(json.dumps(response).encode('utf-8') + b'\n')
                if "error" in response:
                    add_to_log(f"ERR [{method}] {response['error'].get('message')}")
            except socket.timeout: continue
            except json.JSONDecodeError:
                conn.sendall(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}).encode('utf-8') + b'\n')
    except: add_to_log(f'Client handler error: {traceback.format_exc()}')
    finally:
        try: conn.close()
        except: pass
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
    global app, ui, server_thread, stop_event, mcp_custom_event, handlers
    # Reset handlers list to avoid keeping refs to old UI items on reload
    handlers = []
    
    try:
        app = adsk.core.Application.get()
        if app is None:
            raise RuntimeError("Failed to acquire Fusion 360 application handle")
        ui  = app.userInterface
        if ui is None:
            raise RuntimeError("Failed to acquire Fusion 360 user interface handle")
        add_to_log("run() called. Starting initialization...")

        # 1. Setup UI (First, so it appears even if other things fail)
        try:
            cmd_defs = ui.commandDefinitions
            panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
            if not panel:
                # Try fallback panel if SolidScriptsAddinsPanel is missing (some workspaces)
                panel = ui.allToolbarPanels.itemById('ScriptsAddinsPanel')

            # Clean up old UI items correctly
            for cid in ['mcp_settings_cmd', 'mcp_log_view_cmd']:
                old_def = cmd_defs.itemById(cid)
                if old_def:
                    # Remove from panel first
                    if panel:
                        old_ctrl = panel.controls.itemById(cid)
                        if old_ctrl: old_ctrl.deleteMe()
                    old_def.deleteMe()

            # Create new definitions
            settings_cmd = cmd_defs.addButtonDefinition('mcp_settings_cmd', 'MCP Settings', 'Configure MCP server.', RESOURCES_PATH)
            on_settings = SettingsCommandCreatedHandler()
            settings_cmd.commandCreated.add(on_settings)
            handlers.append(on_settings)
            
            log_cmd = cmd_defs.addButtonDefinition('mcp_log_view_cmd', 'View MCP Log', 'View activity log.', RESOURCES_PATH)
            on_log = LogCommandCreatedHandler()
            log_cmd.commandCreated.add(on_log)
            handlers.append(on_log)
            
            # Add to panel
            if panel:
                panel.controls.addCommand(settings_cmd)
                panel.controls.addCommand(log_cmd)
                add_to_log("UI Menu items added successfully.")
            else:
                add_to_log("Warning: Could not find a suitable toolbar panel for UI.")
        except Exception as ui_err:
            add_to_log(f"UI Initialization failed: {traceback.format_exc()}")

        # 2. Register Custom Event
        try:
            # Unregister if previously orphaned
            try: app.unregisterCustomEvent(mcp_custom_event_id)
            except: pass
            
            mcp_custom_event = app.registerCustomEvent(mcp_custom_event_id)
            if mcp_custom_event is None:
                raise RuntimeError("Failed to register MCP custom event")
            on_mcp_event = MCPCustomEventHandler()
            mcp_custom_event.add(on_mcp_event)
            handlers.append(on_mcp_event)
            add_to_log("Custom Event registered.")
        except:
            add_to_log(f"Custom Event registration failed: {traceback.format_exc()}")

        # 3. Start Server
        try:
            stop_event.clear()
            server_thread = threading.Thread(target=server_loop, daemon=True)
            server_thread.start()
            add_to_log("Server thread started.")
        except:
            add_to_log(f"Server start failed: {traceback.format_exc()}")
            
        add_to_log(f"MCP Add-In Version {VERSION} (UI Patch) Initialization Complete.")
    except Exception as fatal_e:
        # We don't have ui yet or it's dead, fall back to file
        with open(LOG_FILE, 'a') as f:
            f.write(f"FATAL ERROR in run(): {traceback.format_exc()}\n")

def stop(context):
    global handlers, mcp_custom_event, server_thread
    try:
        add_to_log('Stopping MCP Add-In...')
        stop_event.set()
        
        # UI Cleanup
        try:
            if ui is not None:
                cmd_defs = ui.commandDefinitions
                panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
                if not panel:
                    panel = ui.allToolbarPanels.itemById('ScriptsAddinsPanel')

                for cid in ['mcp_settings_cmd', 'mcp_log_view_cmd']:
                    if panel:
                        ctrl = panel.controls.itemById(cid)
                        if ctrl:
                            ctrl.deleteMe()
                    cmd = cmd_defs.itemById(cid)
                    if cmd:
                        cmd.deleteMe()
        except: pass

        # Event Cleanup
        try:
            if mcp_custom_event and app is not None:
                app.unregisterCustomEvent(mcp_custom_event_id)
                mcp_custom_event = None
        except: pass
        
        handlers = []
        add_to_log('MCP Add-In Stopped.')
    except:
        with open(LOG_FILE, 'a') as f:
            f.write(f"ERROR in stop(): {traceback.format_exc()}\n")
