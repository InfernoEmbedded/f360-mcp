import adsk.core
import adsk.fusion
import traceback
import threading
import socket
import json
import time

from . import commands

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
            data = conn.recv(4096)
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
                
                # Execute in the main thread is not strictly required if we are just modifying data,
                # but it's highly recommended for Fusion 360 API stability. For simple tests, we can just call.
                # However, adsk.core.Application.executeTextCommand could be used, or custom events.
                # For simplicity in this demo, we'll try direct calls. If it crashes, we'll need a custom event.
                try:
                    dispatch = {
                        'create_sketch': commands.create_sketch,
                        'add_circle': commands.add_circle,
                        'add_line': commands.add_line,
                        'add_rectangle': commands.add_rectangle,
                        'add_arc': commands.add_arc,
                        'add_spline': commands.add_spline,
                        'add_polygon': commands.add_polygon,
                        'add_point': commands.add_point,
                        'add_text': commands.add_text,
                        'apply_constraint': commands.apply_constraint,
                        'add_symmetry_constraint': commands.add_symmetry_constraint,
                        'add_distance_dimension': commands.add_distance_dimension,
                        'add_diameter_dimension': commands.add_diameter_dimension,
                        'add_angular_dimension': commands.add_angular_dimension,
                        'list_sketches': commands.list_sketches,
                        'delete_sketch': commands.delete_sketch,
                        'project_geometry': commands.project_geometry,
                        'offset_geometry': commands.offset_geometry,
                        'delete_sketch_entity': commands.delete_sketch_entity,
                        'trim_sketch_geometry': commands.trim_sketch_geometry,
                        'create_extrude': commands.create_extrude,
                        'create_revolve': commands.create_revolve,
                        'create_sweep': commands.create_sweep,
                        'list_bodies': commands.list_bodies,
                        'combine_bodies': commands.combine_bodies,
                        'create_hole': commands.create_hole,
                        'create_shell': commands.create_shell,
                        'create_fillet': commands.create_fillet,
                        'create_chamfer': commands.create_chamfer,
                        'feature_mirror': commands.feature_mirror,
                        'create_loft': commands.create_loft,
                        'execute_script': commands.execute_script,
                        'create_offset_plane': commands.create_offset_plane,
                        'create_plane_at_angle': commands.create_plane_at_angle,
                        'get_body_properties': commands.get_body_properties,
                        'find_faces': commands.find_faces,
                        'create_user_parameter': commands.create_user_parameter,
                        'list_user_parameters': commands.list_user_parameters,
                        'update_user_parameter': commands.update_user_parameter,
                        'create_component': commands.create_component,
                        'create_rectangular_pattern': commands.create_rectangular_pattern,
                        'create_circular_pattern': commands.create_circular_pattern,
                        'export_model': commands.export_model,
                        'rename_body': commands.rename_body,
                        'list_features': commands.list_features,
                        'rename_feature': commands.rename_feature,
                    }


                    
                    if method in dispatch:
                        result = dispatch[method](app, **params)
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
