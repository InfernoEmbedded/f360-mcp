import adsk.core
import adsk.fusion
import traceback
import threading
import socket
import json
import time

from .commands import (
    registry, sketch, solid, construction, assembly, params, data, query, materials, utils, internal
)
from .commands.base import get_active_design, _get_timeline_health_map, _group_stack

# Globals
app = None
ui  = None
server_thread = None
stop_event = threading.Event()
PORT = 30011

def handle_client(conn, addr):
    app.log(f'Connected by {addr}')
    try:
        while not stop_event.is_set():
            data = conn.recv(8192)
            if not data:
                break
            
            try:
                request = json.loads(data.decode('utf-8'))
                method = request.get('method')
                params = request.get('params', {})
                req_id = request.get('id')
                
                app.log(f"Received method: {method}")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
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
                                    app.log(f"Auto-grouping failed: {str(e)}")
                        
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
                    app.log(f"Error executing command: {traceback.format_exc()}")
                
                conn.sendall(json.dumps(response).encode('utf-8') + b'\n')
            except json.JSONDecodeError:
                conn.sendall(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}).encode('utf-8') + b'\n')
    except Exception as e:
        app.log(f"Client handler exception: {str(e)}")
    finally:
        conn.close()

def server_loop():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind to 127.0.0.1 so it's only accessible locally
            s.bind(('127.0.0.1', PORT))
            s.listen()
            # Set timeout to allow checking stop_event
            s.settimeout(1.0)
            app.log(f"MCP Add-In TCP Server listening on port {PORT}")
            
            while not stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    # Start a thread for each client (though usually just one MCP server)
                    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    app.log(f"Accept error: {str(e)}")
    except Exception as e:
        if app:
            app.log(f"Server loop error: {traceback.format_exc()}")

def run(context):
    global app, ui, server_thread, stop_event
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        stop_event.clear()
        server_thread = threading.Thread(target=server_loop)
        # Daemon thread makes sure it dies when Fusion exits if stop() fails
        server_thread.daemon = True 
        server_thread.start()
        
        ui.messageBox('MCP Add-In Started. Listening on TCP 30011.')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        stop_event.set()
        if server_thread and server_thread.is_alive():
            # The server loop will timeout in 1s and see stop_event.is_set()
            server_thread.join(timeout=2.0)
            
        ui.messageBox('MCP Add-In Stopped.')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
