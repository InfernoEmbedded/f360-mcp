import pytest
from f360_mcp_server.server import create_user_parameter, list_parameters, update_parameter

@pytest.mark.asyncio
async def test_refined_parameter_lifecycle(mock_fusion):
    # 1. Create user param with formula and description
    res_create = await create_user_parameter(
        name="length", 
        expression="100mm", 
        description="Main length"
    )
    assert "Created parameter 'length'" in res_create["message"]
    assert res_create["comment"] == "Main length"
    
    # 2. List all parameters (user and model)
    res_list = await list_parameters()
    params = res_list["parameters"]
    assert len(params) >= 2
    
    # Verify user param
    user_param = next(p for p in params if p["name"] == "width")
    assert user_param["isUserParameter"] is True
    assert user_param["comment"] == "Base width"
    
    # Verify model param
    model_param = next(p for p in params if p["name"] == "d1")
    assert model_param["isUserParameter"] is False
    assert "width * 2" in model_param["expression"]
    
    # 3. Update parameter (expression and description)
    res_update = await update_parameter(
        name="length", 
        expression="120mm", 
        description="Main length updated"
    )
    assert "Updated parameter 'length'" in res_update["message"]
    # Mock return matches our update
    assert res_update["comment"] == "Main length updated"
    
    # 4. Update model parameter description only
    res_update_model = await update_parameter(
        name="d1", 
        description="Driven dimension"
    )
    assert "Updated parameter 'd1'" in res_update_model["message"]
    assert res_update_model["comment"] == "Driven dimension"
