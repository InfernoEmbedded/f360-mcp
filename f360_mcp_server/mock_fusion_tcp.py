import asyncio
import json
import logging
import os
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MockFusion")

# Default metadata for basic tests
DEFAULT_METADATA = {
    "create_sketch": {"doc": "Creates a sketch.", "parameters": [{"name": "plane_name", "has_default": True, "default": "XY", "annotation": "Any"}]},
    "add_circle": {"doc": "Adds a circle.", "parameters": [{"name": "sketch_name", "has_default": False, "default": None, "annotation": "Any"}, {"name": "x", "has_default": False, "default": None, "annotation": "Any"}, {"name": "y", "has_default": False, "default": None, "annotation": "Any"}, {"name": "radius", "has_default": False, "default": None, "annotation": "Any"}]},
    "export_model": {"parameters": [{"name": "file_path"}, {"name": "send_to_mcp", "has_default": True, "default": False}, {"name": "local_file_path", "has_default": True, "default": None}]},
    "execute_script": {"parameters": [{"name": "script_code"}]},
    "reload_addin": {"parameters": []},
    "_get_command_metadata": {"parameters": []}
}

def load_metadata():
    path = "/tmp/metadata.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata from {path}: {e}")
    return DEFAULT_METADATA

FULL_METADATA = load_metadata()

class MockFusionServer:
    def __init__(self, host=None, port=None):
        self.host = host if host is not None else os.environ.get('F360_ADDIN_HOST', '127.0.0.1')
        self.port = int(port) if port is not None else int(os.environ.get('F360_ADDIN_PORT', 30011))
        self.server = None
        self.last_request = None
        self.loop = None
        self.thread = None
        self.stop_event = asyncio.Event()
        self.current_group_name = "Test Group"

    async def handle_client(self, reader, writer):
        try:
            data = await reader.read(16384)
            if not data:
                return
            
            message = data.decode('utf-8').strip()
            request = json.loads(message)
            self.last_request = request
            method = request.get('method')
            params = request.get('params', {})
            logger.info(f"Received request: {method}")

            # Specialize responses first (priority matching)
            if method == '_get_command_metadata':
                meta = FULL_METADATA.copy()
                solid_meta = {
                    "split_body": [{"name": "body_name"}, {"name": "split_tool_name"}, {"name": "is_surface_tool", "has_default": True, "default": True}],
                    "create_extrude": [{"name": "sketch_name"}, {"name": "distance"}, {"name": "operation", "has_default": True, "default": "new_body"}, {"name": "profile_index", "has_default": True, "default": 0}],
                    "create_revolve": [{"name": "sketch_name"}, {"name": "axis_ent_type"}, {"name": "axis_ent_idx"}, {"name": "angle"}],
                    "create_sweep": [{"name": "profile_sketch_name"}, {"name": "path_sketch_name"}, {"name": "path_ent_type"}, {"name": "path_ent_idx"}],
                    "create_loft": [{"name": "profiles_info"}],
                    "create_hole": [{"name": "sketch_name"}, {"name": "point_idx"}, {"name": "diameter"}, {"name": "depth"}],
                    "create_shell": [{"name": "body_name"}, {"name": "thickness"}],
                    "create_fillet": [{"name": "body_name"}, {"name": "radius"}],
                    "create_chamfer": [{"name": "body_name"}, {"name": "distance"}],
                    "feature_mirror": [{"name": "body_name"}, {"name": "plane_name"}],
                    "combine_bodies": [{"name": "target_body_name"}, {"name": "tool_body_names"}, {"name": "operation", "has_default": True, "default": "join"}],
                    "scale_body": [{"name": "body_name"}, {"name": "scale_factor"}],
                    "create_thread": [{"name": "body_name"}, {"name": "face_index", "has_default": True, "default": 0}, {"name": "is_modeled", "has_default": True, "default": True}],
                    "move_body": [{"name": "body_name"}, {"name": "dx"}, {"name": "dy"}, {"name": "dz"}],
                    "measure_interference": [{"name": "body_names"}],
                    "create_rib": [{"name": "sketch_name"}, {"name": "thickness"}],
                    "create_web": [{"name": "sketch_name"}, {"name": "thickness"}],
                    "create_emboss": [{"name": "sketch_name"}, {"name": "body_name"}, {"name": "depth"}],
                    "import_mesh": [{"name": "file_path"}],
                    "convert_mesh_to_solid": [{"name": "body_name"}, {"name": "method", "has_default": True, "default": "prismatic"}],
                    "create_joint": [{"name": "component1_name"}, {"name": "component2_name"}, {"name": "joint_type", "has_default": True, "default": "rigid"}, {"name": "offset_x", "has_default": True, "default": 0}, {"name": "offset_y", "has_default": True, "default": 0}, {"name": "offset_z", "has_default": True, "default": 0}],
                    "create_as_built_joint": [{"name": "component1_name"}, {"name": "component2_name"}, {"name": "joint_type", "has_default": True, "default": "rigid"}],
                    "reload_addin": []
                }
                for cmd, params_list in solid_meta.items():
                    if cmd not in meta:
                        meta[cmd] = {"parameters": params_list}
                result = meta
            elif method == 'start_timeline_group':
                 if params.get('name'):
                     self.current_group_name = params.get('name')
                 result = {"message": f"Successfully started timeline group '{self.current_group_name}'"}
            elif method == 'stop_timeline_group':
                 result = {"message": f"Successfully Created timeline group '{self.current_group_name}'"}
            elif method == 'list_bodies':
                result = {"bodies": [{"name": "Body 1", "index": 0}]}
            elif method == 'list_sketches':
                result = {"sketches": [{"name": "Sketch 1"}]}
            elif method == 'list_features':
                result = {"features": [{"name": "Extrude 1", "type": "Extrude", "index": 0}]}
            elif method in ['list_parameters', 'list_user_parameters']:
                result = {"parameters": [
                    {"name": "width", "expression": "10cm", "value": 10.0, "unit": "cm", "comment": "Base width", "isUserParameter": True},
                    {"name": "d1", "expression": "width * 2", "value": 20.0, "unit": "cm", "comment": "Model parameter", "isUserParameter": False},
                    {"name": "length", "expression": "100mm", "value": 10.0, "unit": "mm", "comment": "Main length", "isUserParameter": True}
                ]}
            elif method == 'list_materials':
                result = {"materials": [{"name": "Steel", "library": "Design"}]}
            elif method == 'list_appearances':
                result = {"appearances": [{"name": "Paint - Red", "library": "Design"}]}
            elif method == 'list_projects':
                result = {"projects": [{"name": "Default Project", "id": "p1"}, {"name": "Test Project", "id": "p2"}], "project_id": "p3"}
            elif method == 'list_components':
                result = {"components": [{"name": "Component 1", "id": "c1"}]}
            elif method == 'list_construction':
                result = {"construction": [{"name": "Plane 1", "id": "cp1"}]}
            elif method == 'export_model':
                if params.get('send_to_mcp'):
                    import base64
                    result = {
                        "message": "Export success",
                        "file_content_base64": base64.b64encode(b"dummy_stl_content").decode('utf-8')
                    }
                else:
                    result = {"message": f"Successfully exported to {params.get('file_path')}"}
            elif method == 'capture_screenshot':
                import base64
                result = {
                    "message": "Screenshot saved",
                    "file_content_base64": base64.b64encode(b"dummy_image_content").decode('utf-8'),
                    "local_file_path": params.get('local_file_path')
                }
                if params.get('local_file_path'):
                    result["message"] = f"Screenshot saved to {params['local_file_path']}"
            elif method == 'get_design_health':
                result = {"message": "Design is healthy."}
            elif method == 'get_sketch_info':
                # Tests expect 'profiles' and specific summary in sketch info
                result = {
                    "sketch_name": params.get("sketch_name", "Unknown"), 
                    "profiles": [{"index": 0, "area": 10.0}, {"index": 1, "area": 5.0}], 
                    "curves": [], 
                    "points": [],
                    "curves_summary": [{"name": "Line", "count": 4}, {"name": "Circle", "count": 1}],
                    "profiles_count": 2,
                    "curves_count": 5,
                    "points_count": 0
                }
            elif method == 'get_body_properties':
                result = {"body_name": params.get("body_name", "Unknown"), "mass_kg": 1.0}
            elif method == 'get_face_info' or method == 'find_faces':
                result = {
                    "faces": [{"id": 0, "area": 1.0, "type": "Planar"}], 
                    "body_name": params.get("body_name", "Unknown"),
                    "faces_count": 1
                }
            elif method == 'get_edge_info':
                result = {
                    "body_name": params.get("body_name", "Unknown"), 
                    "edges": [{"id": 0, "length": 1.0, "type": "Line"}]
                }
            elif method == 'undo':
                result = {"message": f"Successfully Undid {params.get('steps', 1)} steps"}
            elif method == 'redo':
                result = {"message": f"Successfully Redid {params.get('steps', 1)} steps"}
            elif method == 'save_design':
                result = {"message": "Design saved successfully"}
            elif method == 'create_joint':
                 jt = params.get('joint_type', 'rigid')
                 result = {"message": f"Created {jt} joint", "joint_name": f"{jt.capitalize()}1"}
            elif method == 'create_as_built_joint':
                 jt = params.get('joint_type', 'rigid')
                 result = {"message": f"Created as-built {jt} joint", "joint_name": f"{jt.capitalize()}1"}
            elif method == 'create_folder':
                 result = {"message": f"Successfully Created folder '{params.get('folder_name')}'", "folder_id": "new_folder_id"}
            elif method == 'create_new_design':
                 if params.get('project_name'):
                     result = {"message": f"Successfully Created and saved design '{params.get('name')}'", "status": "saved"}
                 else:
                     result = {"message": f"Successfully Created new unsaved design '{params.get('name')}'", "status": "unsaved"}
            elif method == 'create_project':
                 result = {"message": f"Successfully Created project '{params.get('name')}'", "project_id": "new_proj_id"}
            elif method in ['create_user_parameter', 'create_parameter']:
                 result = {
                     "message": f"Successfully Created parameter '{params.get('name')}'", 
                     "name": params.get('name'),
                     "comment": params.get('description', ''),
                     "expression": params.get('expression', '')
                 }
            elif method in ['update_parameter', 'update_user_parameter']:
                 result = {
                     "message": f"Successfully Updated parameter '{params.get('name')}'", 
                     "name": params.get('name'),
                     "comment": params.get('description', ''),
                     "expression": params.get('expression', '')
                 }
            elif method == 'delete_user_parameter':
                 result = {"message": f"Successfully deleted parameter {params.get('name')}"}
            elif method == 'shutdown':
                result = {"message": "Shutting down mock server..."}
                if self.loop: self.loop.call_later(0.1, self.loop.stop)
            elif method == 'reload_addin':
                result = {"message": "Reloader script executed. Add-in should restart momentarily."}
            else:
                # Default generic result
                result = {"message": f"Successfully executed {method}"}
                
                # Smart generic message for tests that check 'assert "X" in message'
                details = []
                for k, v in params.items():
                    if k not in ["sketch_name", "body_name", "local_file_path", "send_to_mcp"]:
                        details.append(f"{k}='{v}'")
                
                if "name" in params:
                    result["message"] = f"Successfully Created {method.replace('create_', '')} '{params['name']}'"
                elif "text" in params:
                     result["message"] = f"Successfully Added text '{params['text']}'"
                elif details:
                    result["message"] += f" with {', '.join(details)}"

            response = {
                "jsonrpc": "2.0",
                "id": request.get('id'),
                "result": result
            }
            
            writer.write(json.dumps(response).encode('utf-8') + b'\n')
            await writer.drain()
        except Exception as e:
            logger.error(f"Error handling client: {str(e)}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        protocol_server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        self.server = protocol_server
        self.host, self.port = protocol_server.sockets[0].getsockname()
        os.environ['F360_ADDIN_PORT'] = str(self.port)
        logger.info(f"Mock Fusion Server started on {self.host}:{self.port}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Mock Fusion Server stopped")

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start())
        self.loop.run_forever()

    def start_threaded(self):
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        import time
        while self.port == 0 or 'F360_ADDIN_PORT' not in os.environ:
            time.sleep(0.1)

    def stop_threaded(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=1)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    mock = MockFusionServer()
    try:
        loop.run_until_complete(mock.start())
        loop.run_forever()
    except KeyboardInterrupt: pass
    finally: loop.run_until_complete(mock.stop())
