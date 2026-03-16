import pytest
import pytest_asyncio
from f360_mcp_server.server import get_face_info, get_edge_info, get_sketch_info, undo, redo, save_design, get_body_properties
from test_utils import compare_command_logs

@pytest.mark.anyio
async def test_topology_queries(mock_fusion, recorded_commands):
    # 1. Get properties
    await get_body_properties(body_name="Body 1")
    
    # 2. Get face info
    await get_face_info(body_name="Body 1")
    
    # 3. Get edge info
    await get_edge_info(body_name="Body 1")
    
    compare_command_logs("test_topology_queries", recorded_commands)
