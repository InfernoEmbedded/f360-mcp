import pytest
from f360_mcp_server.server import create_user_parameter, list_user_parameters, update_user_parameter, delete_user_parameter

@pytest.mark.asyncio
async def test_parameter_lifecycle(mock_fusion):
    # 1. Create
    res_create = await create_user_parameter(name="width", expression="10cm")
    assert "Created parameter 'width'" in res_create["message"]
    
    # 2. List
    res_list = await list_user_parameters()
    # Mock return matches the one in mock_fusion_tcp.py
    # Actually mock_fusion_tcp.py has a fixed dict for list_user_parameters?
    # No, it seems I didn't update list_user_parameters in mock.
    # Wait, let me check mock_fusion_tcp.py again.
    assert "parameters" in res_list
    
    # 3. Update
    res_update = await update_user_parameter(name="width", expression="15cm")
    assert "Updated parameter 'width'" in res_update["message"]
    
    # 4. Delete
    res_delete = await delete_user_parameter(name="width")
    assert "Successfully deleted parameter width" in res_delete["message"]
