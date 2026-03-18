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
    # Sketch
    "create_sketch": {"doc": "Creates a sketch.", "parameters": [
        {"name": "name", "has_default": False},
        {"name": "plane_name", "has_default": True, "default": "XY"},
        {"name": "body_name", "has_default": True, "default": None},
        {"name": "face_index", "has_default": True, "default": None}
    ]},
    "add_line": {"parameters": [{"name": "sketch_name"}, {"name": "x1"}, {"name": "y1"}, {"name": "x2"}, {"name": "y2"}]},
    "add_circle": {"doc": "Adds a circle.", "parameters": [{"name": "sketch_name"}, {"name": "x"}, {"name": "y"}, {"name": "radius"}]},
    "add_rectangle": {"parameters": [{"name": "sketch_name"}, {"name": "x1"}, {"name": "y1"}, {"name": "x2"}, {"name": "y2"}, {"name": "x3", "has_default": True, "default": None}, {"name": "y3", "has_default": True, "default": None}, {"name": "rect_type", "has_default": True, "default": "two_point"}]},
    "add_arc": {"parameters": [{"name": "sketch_name"}, {"name": "x1"}, {"name": "y1"}, {"name": "x2"}, {"name": "y2"}, {"name": "x3"}, {"name": "y3"}, {"name": "arc_type", "has_default": True, "default": "three_point"}]},
    "add_slot": {"parameters": [{"name": "sketch_name"}, {"name": "x1"}, {"name": "y1"}, {"name": "x2"}, {"name": "y2"}, {"name": "width"}]},
    "add_spline": {"parameters": [{"name": "sketch_name"}, {"name": "points"}]},
    "add_polygon": {"parameters": [{"name": "sketch_name"}, {"name": "center_x"}, {"name": "center_y"}, {"name": "num_sides"}, {"name": "vertex_x"}, {"name": "vertex_y"}, {"name": "poly_type", "has_default": True, "default": "inscribed"}]},
    "add_ellipse": {"parameters": [{"name": "sketch_name"}, {"name": "center_x"}, {"name": "center_y"}, {"name": "major_x"}, {"name": "major_y"}, {"name": "minor_x"}, {"name": "minor_y"}]},
    "add_point": {"parameters": [{"name": "sketch_name"}, {"name": "x"}, {"name": "y"}]},
    "add_text": {"parameters": [{"name": "sketch_name"}, {"name": "text"}, {"name": "x"}, {"name": "y"}, {"name": "height", "has_default": True, "default": 0.5}]},
    "apply_constraint": {"parameters": [{"name": "sketch_name"}, {"name": "constraint_type"}, {"name": "ent1_type"}, {"name": "ent1_idx"}, {"name": "ent2_type", "has_default": True, "default": None}, {"name": "ent2_idx", "has_default": True, "default": None}]},
    "add_symmetry_constraint": {"parameters": [{"name": "sketch_name"}, {"name": "ent1_type"}, {"name": "ent1_idx"}, {"name": "ent2_type"}, {"name": "ent2_idx"}, {"name": "sym_line_type"}, {"name": "sym_line_idx"}]},
    "add_distance_dimension": {"parameters": [{"name": "sketch_name"}, {"name": "ent1_type"}, {"name": "ent1_idx"}, {"name": "ent2_type"}, {"name": "ent2_idx"}, {"name": "text_x"}, {"name": "text_y"}, {"name": "orientation", "has_default": True, "default": "aligned"}]},
    "add_radial_dimension": {"parameters": [{"name": "sketch_name"}, {"name": "ent_type"}, {"name": "ent_idx"}, {"name": "text_x"}, {"name": "text_y"}]},
    "add_diameter_dimension": {"parameters": [{"name": "sketch_name"}, {"name": "ent_type"}, {"name": "ent_idx"}, {"name": "text_x"}, {"name": "text_y"}]},
    "add_angular_dimension": {"parameters": [{"name": "sketch_name"}, {"name": "line1_idx"}, {"name": "line2_idx"}, {"name": "text_x"}, {"name": "text_y"}]},
    "project_geometry": {"parameters": [{"name": "sketch_name"}, {"name": "ent_type"}, {"name": "ent_idx"}, {"name": "from_sketch_name", "has_default": True, "default": None}]},
    "offset_geometry": {"parameters": [{"name": "sketch_name"}, {"name": "ent_type"}, {"name": "ent_idx"}, {"name": "offset_distance"}]},
    "delete_sketch_entity": {"parameters": [{"name": "sketch_name"}, {"name": "ent_type"}, {"name": "ent_idx"}]},
    "trim_sketch_geometry": {"parameters": [{"name": "sketch_name"}, {"name": "ent_type"}, {"name": "ent_idx"}, {"name": "x"}, {"name": "y"}]},
    "list_sketches": {"parameters": []},
    "delete_sketch": {"parameters": [{"name": "sketch_name"}]},
    "rename_sketch": {"parameters": [{"name": "old_name"}, {"name": "new_name"}]},

    # Utils / Global
    "undo": {"parameters": [{"name": "steps", "has_default": True, "default": 1}]},
    "redo": {"parameters": [{"name": "steps", "has_default": True, "default": 1}]},
    "save_design": {"parameters": [{"name": "description", "has_default": True, "default": "Saved via MCP"}]},
    "capture_screenshot": {"parameters": [{"name": "file_path"}, {"name": "width", "has_default": True, "default": 1280}, {"name": "height", "has_default": True, "default": 720}, {"name": "send_to_mcp", "has_default": True, "default": False}]},
    "execute_script": {"parameters": [{"name": "script_code"}]},
    "reload_addin": {"parameters": []},
    "start_timeline_group": {"parameters": [{"name": "name"}]},
    "stop_timeline_group": {"parameters": []},
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
                # Detailed metadata for specialized tests
                detailed_meta = {
                    # Solid Features
                    "split_body": [{"name": "name"}, {"name": "body_name"}, {"name": "split_tool_name"}, {"name": "is_surface_tool", "has_default": True, "default": True}],
                    "create_extrude": [{"name": "name"}, {"name": "sketch_name"}, {"name": "distance"}, {"name": "operation", "has_default": True, "default": "new_body"}, {"name": "profile_index", "has_default": True, "default": 0}],
                    "create_revolve": [{"name": "name"}, {"name": "sketch_name"}, {"name": "axis_ent_type"}, {"name": "axis_ent_idx"}, {"name": "angle"}, {"name": "operation", "has_default": True, "default": "new_body"}, {"name": "profile_index", "has_default": True, "default": 0}],
                    "create_sweep": [{"name": "name"}, {"name": "profile_sketch_name"}, {"name": "path_sketch_name"}, {"name": "path_ent_type"}, {"name": "path_ent_idx"}, {"name": "operation", "has_default": True, "default": "new_body"}, {"name": "profile_index", "has_default": True, "default": 0}],
                    "create_loft": [{"name": "name"}, {"name": "profiles_info"}],
                    "create_hole": [{"name": "name"}, {"name": "sketch_name"}, {"name": "point_idx"}, {"name": "diameter"}, {"name": "depth"}],
                    "create_shell": [{"name": "name"}, {"name": "body_name"}, {"name": "thickness"}],
                    "create_fillet": [{"name": "name"}, {"name": "body_name"}, {"name": "radius"}],
                    "create_chamfer": [{"name": "name"}, {"name": "body_name"}, {"name": "distance"}],
                    "feature_mirror": [{"name": "name"}, {"name": "body_name"}, {"name": "plane_name"}],
                    "create_rectangular_pattern": [{"name": "name"}, {"name": "body_name"}, {"name": "count_x"}, {"name": "count_y"}, {"name": "distance_x"}, {"name": "distance_y"}],
                    "create_circular_pattern": [{"name": "name"}, {"name": "body_name"}, {"name": "axis_name"}, {"name": "count"}, {"name": "angle_deg"}],
                    "combine_bodies": [{"name": "name"}, {"name": "target_body_name"}, {"name": "tool_body_names"}, {"name": "operation", "has_default": True, "default": "join"}],
                    "rename_body": [{"name": "old_name"}, {"name": "new_name"}],
                    "delete_body": [{"name": "body_name"}],
                    "list_bodies": [],
                    "rename_feature": [{"name": "old_name"}, {"name": "new_name"}],
                    "delete_feature": [{"name": "feature_name"}],
                    "list_features": [],
                    "scale_body": [{"name": "name"}, {"name": "body_name"}, {"name": "scale_factor"}],
                    "create_thread": [{"name": "name"}, {"name": "body_name"}, {"name": "face_index", "has_default": True, "default": 0}, {"name": "is_modeled", "has_default": True, "default": True}],
                    "move_body": [{"name": "name"}, {"name": "body_name"}, {"name": "dx"}, {"name": "dy"}, {"name": "dz"}],
                    "create_rib": [{"name": "name"}, {"name": "sketch_name"}, {"name": "thickness"}],
                    "create_web": [{"name": "name"}, {"name": "sketch_name"}, {"name": "thickness"}],
                    "create_emboss": [{"name": "name"}, {"name": "sketch_name"}, {"name": "body_name"}, {"name": "depth"}],
                    "compute_all": [],

                    # Assembly
                    "create_component": [{"name": "name"}],
                    "list_components": [],
                    "rename_component": [{"name": "old_name"}, {"name": "new_name"}],
                    "delete_component": [{"name": "occurrence_name"}],
                    "create_joint": [{"name": "name"}, {"name": "component1_name"}, {"name": "component2_name"}, {"name": "joint_type", "has_default": True, "default": "rigid"}, {"name": "offset_x", "has_default": True, "default": 0}, {"name": "offset_y", "has_default": True, "default": 0}, {"name": "offset_z", "has_default": True, "default": 0}],
                    "create_as_built_joint": [{"name": "name"}, {"name": "component1_name"}, {"name": "component2_name"}, {"name": "joint_type", "has_default": True, "default": "rigid"}],
                    "get_active_component": [],

                    # Data
                    "list_projects": [],
                    "create_project": [{"name": "name"}],
                    "create_folder": [{"name": "project_name"}, {"name": "folder_name"}, {"name": "parent_folder_path", "has_default": True, "default": None}],
                    "list_designs": [{"name": "project_name"}, {"name": "folder_path", "has_default": True, "default": None}],
                    "open_design": [{"name": "project_name"}, {"name": "name"}, {"name": "folder_path", "has_default": True, "default": None}],
                    "create_new_design": [{"name": "name"}, {"name": "project_name", "has_default": True, "default": None}, {"name": "folder_path", "has_default": True, "default": None}],
                    "close_document": [{"name": "save", "has_default": True, "default": False}],
                    "close_all_documents": [{"name": "save", "has_default": True, "default": False}],
                    "export_model": [{"name": "file_path"}, {"name": "file_type", "has_default": True, "default": "step"}, {"name": "body_name", "has_default": True, "default": None}, {"name": "send_to_mcp", "has_default": True, "default": False}],

                    # Materials
                    "list_materials": [],
                    "apply_material": [{"name": "body_name"}, {"name": "material_name"}],
                    "list_appearances": [],
                    "apply_appearance": [{"name": "body_name"}, {"name": "appearance_name"}],

                    # Parameters
                    "create_user_parameter": [{"name": "name"}, {"name": "expression"}, {"name": "unit", "has_default": True, "default": ""}, {"name": "description", "has_default": True, "default": ""}],
                    "list_user_parameters": [],
                    "list_parameters": [],
                    "update_parameter": [{"name": "name"}, {"name": "expression", "has_default": True, "default": None}, {"name": "description", "has_default": True, "default": None}],
                    "update_user_parameter": [{"name": "name"}, {"name": "expression", "has_default": True, "default": None}, {"name": "description", "has_default": True, "default": None}],
                    "delete_user_parameter": [{"name": "name"}],

                    # Query / Topology / Health
                    "get_face_info": [{"name": "body_name"}],
                    "get_edge_info": [{"name": "body_name"}],
                    "get_sketch_info": [{"name": "sketch_name"}],
                    "get_body_properties": [{"name": "body_name"}],
                    "get_object_hierarchy": [],
                    "measure_interference": [{"name": "body_names"}],
                    "get_design_health": [],

                    # Construction
                    "create_offset_plane": [{"name": "name"}, {"name": "base_plane"}, {"name": "offset"}],
                    "create_plane_at_angle": [{"name": "name"}, {"name": "axis_name"}, {"name": "angle_deg"}],
                    "list_construction": [],
                    "rename_construction": [{"name": "old_name"}, {"name": "new_name"}, {"name": "type", "has_default": True, "default": "plane"}],
                    "delete_construction": [{"name": "name"}, {"name": "type", "has_default": True, "default": "plane"}],

                    # Mesh
                    "import_mesh": [{"name": "file_path"}],
                    "convert_mesh_to_solid": [{"name": "name"}, {"name": "body_name"}, {"name": "method", "has_default": True, "default": "prismatic"}],
                }
                for cmd, params_list in detailed_meta.items():
                    if cmd not in meta:
                        meta[cmd] = {
                            "doc": f"Mock {cmd}",
                            "parameters": [
                                {
                                    "name": p["name"],
                                    "has_default": p.get("has_default", False),
                                    "default": p.get("default"),
                                    "annotation": "Any"
                                } for p in params_list
                            ]
                        }
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
                result = {"materials": [
                    {"name": "Steel", "library": "Design", "is_downloaded": True},
                    {"name": "Aluminum", "library": "Fusion 360 Material Library", "is_downloaded": False}
                ]}
            elif method == 'list_appearances':
                result = {"appearances": [
                    {"name": "Paint - Red", "library": "Design", "is_downloaded": True, "has_texture": False},
                    {"name": "Chrome", "library": "Fusion 360 Appearance Library", "is_downloaded": False, "has_texture": True}
                ]}
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
            elif method == 'get_object_hierarchy':
                result = {"hierarchy": {
                    "name": "Root",
                    "type": "Component",
                    "design_name": "Root",
                    "design_type": "ParametricDesignType",
                    "bodies": [{"name": "Body 1", "type": "BRepBody", "is_visible": True}],
                    "sketches": [{"name": "Sketch 1", "type": "Sketch", "profiles_count": 1, "is_visible": True}],
                    "features": [{"name": "Extrude 1", "type": "ExtrudeFeature", "is_suppressed": False}],
                    "children": [{
                        "name": "Component 1",
                        "type": "Component",
                        "occurrence": "Component 1:1",
                        "is_visible": True,
                        "bodies": [{"name": "Body 1", "type": "BRepBody", "is_visible": True}]
                    }]
                }}
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
            elif method == 'close_document':
                result = {"message": "Closed document 'MockDoc'."}
            elif method == 'close_all_documents':
                result = {"message": "Closed 1 document(s).", "closed": ["MockDoc"]}
            else:
                # Default generic result
                result = {"message": f"Successfully executed {method}"}
                
                # Smart generic message for tests that check 'assert "X" in message'
                details = []
                for k, v in params.items():
                    if k not in ["sketch_name", "body_name", "local_file_path", "send_to_mcp"]:
                        details.append(f"{k}='{v}'")
                
                if "name" in params:
                    name_val = params['name']
                    result["message"] = f"Successfully Created {method.replace('create_', '')} '{name_val}'"
                    if method == "create_sketch":
                        result["sketch_name"] = name_val
                    elif method == "create_new_design":
                        result["design_name"] = name_val
                    else:
                        # Default for most solid features
                        result["feature_name"] = name_val
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
