import pytest
from f360_mcp_server.server import create_user_parameter, list_user_parameters, update_user_parameter, delete_user_parameter
from test_utils import compare_command_logs

@pytest.mark.anyio
async def test_parameter_management(mock_fusion, recorded_commands):
    # 1. Create
    res_create = await create_user_parameter(name="width", expression="10cm")
    assert "Created parameter 'width'" in res_create["message"]
    
    # 2. List
    res_list = await list_user_parameters()
    assert "parameters" in res_list
    
    # 3. Update
    res_update = await update_user_parameter(name="width", expression="15cm")
    assert "Updated parameter 'width'" in res_update["message"]
    
    # 4. Delete
    res_delete = await delete_user_parameter(name="width")
    assert "Successfully deleted parameter width" in res_delete["message"]
    
    compare_command_logs("test_parameter_management", recorded_commands)
