import asyncio
import json
import logging
import os
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MockFusion")

class MockFusionServer:
    def __init__(self, host=None, port=None):
        self.host = host if host is not None else os.environ.get('F360_ADDIN_HOST', '127.0.0.1')
        self.port = int(port) if port is not None else int(os.environ.get('F360_ADDIN_PORT', 30011))
        self.server = None
        self.last_request = None
        self.loop = None
        self.thread = None
        self.stop_event = asyncio.Event()

    async def handle_client(self, reader, writer):
        try:
            data = await reader.read(8192)
            if not data:
                return
            
            message = data.decode('utf-8').strip()
            request = json.loads(message)
            self.last_request = request
            method = request.get('method')
            params = request.get('params', {})
            logger.info(f"Received request: {method}")

            # Generic success response for all methods
            result = {"message": f"Successfully executed {method}"}

            # Specialize some responses if needed
            if method == 'list_bodies':
                result = {"bodies": [{"name": "Body 1", "index": 0}]}
            elif method == 'list_sketches':
                result = {"sketches": [{"name": "Sketch 1"}]}
            elif method == 'list_features':
                result = {"features": [{"name": "Extrude 1", "type": "Extrude", "index": 0}]}
            elif method == 'rename_construction':
                result = {"message": f"Successfully renamed {params.get('type', 'plane')} {params['old_name']} to {params['new_name']}"}
            elif method == 'delete_construction':
                result = {"message": f"Successfully deleted {params.get('type', 'plane')} {params['name']}"}
            elif method == 'create_user_parameter':
                result = {
                    "message": f"Created parameter '{params.get('name')}' = {params.get('expression')}", 
                    "name": params.get('name'), 
                    "value": 10.0,
                    "comment": params.get('comment', "")
                }
            elif method == 'update_parameter':
                result = {
                    "message": f"Updated parameter '{params.get('name')}'", 
                    "name": params.get('name'), 
                    "value": 15.0,
                    "comment": params.get('comment') if params.get('comment') is not None else "Updated description"
                }
            elif method == 'list_parameters':
                result = {"parameters": [
                    {"name": "width", "expression": "10cm", "value": 10.0, "unit": "cm", "comment": "Base width", "isUserParameter": True},
                    {"name": "d1", "expression": "width * 2", "value": 20.0, "unit": "cm", "comment": "Model parameter", "isUserParameter": False}
                ]}
            elif method == 'list_materials':
                result = {"materials": [{"name": "Steel", "library": "Design"}, {"name": "Aluminum", "library": "Fusion 360 Material Library"}]}
            elif method == 'apply_material':
                result = {"message": f"Successfully applied material '{params['material_name']}' to body '{params['body_name']}'."}
            elif method == 'list_appearances':
                result = {"appearances": [{"name": "Paint - Red", "library": "Design"}, {"name": "Chrome", "library": "Fusion 360 Appearance Library"}]}
            elif method == 'apply_appearance':
                result = {"message": f"Successfully applied appearance '{params['appearance_name']}' to body '{params['body_name']}'."}
            elif method == 'export_model':
                if params.get('send_to_mcp'):
                    import base64
                    result = {
                        "message": "Export success",
                        "file_content_base64": base64.b64encode(b"dummy_stl_content").decode('utf-8')
                    }
            elif method == 'get_design_health':
                result = {"message": "Design is healthy. No errors or warnings in timeline."}
            elif method == 'start_timeline_group':
                result = {"message": f"Started timeline group '{params.get('name', 'Unnamed')}'"}
            elif method == 'stop_timeline_group':
                result = {"message": "Created timeline group 'Test Group' with 1 items."}
            elif method == 'shutdown':
                result = {"message": "Shutting down mock server..."}
                # Use a small delay to allow sending response before stopping
                if self.loop:
                    self.loop.call_later(0.1, self.loop.stop)
                else:
                    asyncio.get_event_loop().call_later(0.1, asyncio.get_event_loop().stop)
            elif method == 'get_face_info':
                result = {"body_name": params.get("body_name"), "faces": [{"index": 0, "area": 3.14, "type": "Planar"}]}
            elif method == 'get_edge_info':
                result = {"body_name": params.get("body_name"), "edges": [{"index": 0, "length": 1.0, "type": "Line"}]}
            elif method == 'get_sketch_info':
                result = {"sketch_name": params.get("sketch_name"), "profiles": [{"index": 0, "area": 1.0}], "curves_summary": [{"count": 4}]}
            elif method == 'undo':
                result = {"message": f"Undid {params.get('steps', 1)} steps."}
            elif method == 'redo':
                result = {"message": f"Redid {params.get('steps', 1)} steps."}
            elif method == 'save_design':
                result = {"message": "Design saved successfully."}
            elif method == 'create_joint':
                result = {"message": f"Created {params.get('joint_type', 'rigid')} joint.", "joint_name": "Joint1"}
            elif method == 'create_as_built_joint':
                result = {"message": f"Created as-built {params.get('joint_type', 'rigid')} joint.", "joint_name": "Joint1"}
            elif method == 'capture_screenshot':
                result = {"message": f"Screenshot saved to {params.get('file_path')}", "file_path": params.get('file_path')}
                if params.get('send_to_mcp'):
                    result["file_content_base64"] = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==" # 1x1 png
            elif method == 'list_projects':
                result = {"projects": [
                    {"name": "Admin Project", "id": "proj1", "hub_name": "My Hub"},
                    {"name": "Test Project", "id": "proj2", "hub_name": "My Hub"}
                ]}
            elif method == 'create_project':
                result = {"message": f"Created project '{params['name']}'", "project_id": "new_proj_id"}
            elif method == 'create_folder':
                result = {"message": f"Created folder '{params['folder_name']}'", "folder_id": "new_folder_id"}
            elif method == 'create_new_design':
                if params.get('project_name'):
                    result = {"message": f"Created and saved design '{params['name']}'", "status": "saved"}
                else:
                    result = {"message": f"Created new unsaved design '{params['name']}'", "status": "unsaved"}

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
        # Store actual host/port (important if port was 0)
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
        # Wait for port to be set
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
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(mock.stop())
