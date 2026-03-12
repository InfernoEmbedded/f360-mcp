import pytest
from server import (
    list_bodies, rename_body, delete_body,
    list_features, rename_feature, delete_feature,
    list_components, rename_component, delete_component,
    list_construction, rename_construction, delete_construction,
    delete_user_parameter
)

@pytest.mark.asyncio
async def test_body_management(mock_fusion):
    await list_bodies()
    assert mock_fusion.last_request["method"] == "list_bodies"
    
    await rename_body(old_name="Body 1", new_name="NewBody")
    assert mock_fusion.last_request["method"] == "rename_body"
    
    await delete_body(body_name="NewBody")
    assert mock_fusion.last_request["method"] == "delete_body"

@pytest.mark.asyncio
async def test_feature_management(mock_fusion):
    await list_features()
    assert mock_fusion.last_request["method"] == "list_features"
    
    await rename_feature(old_name="F1", new_name="F2")
    assert mock_fusion.last_request["method"] == "rename_feature"
    
    await delete_feature(feature_name="F2")
    assert mock_fusion.last_request["method"] == "delete_feature"

@pytest.mark.asyncio
async def test_component_management(mock_fusion):
    await list_components()
    assert mock_fusion.last_request["method"] == "list_components"
    
    await rename_component(old_name="C1", new_name="C2")
    assert mock_fusion.last_request["method"] == "rename_component"
    
    await delete_component(occurrence_name="C1:1")
    assert mock_fusion.last_request["method"] == "delete_component"

@pytest.mark.asyncio
async def test_construction_management(mock_fusion):
    await list_construction()
    assert mock_fusion.last_request["method"] == "list_construction"
    
    await rename_construction(old_name="P1", new_name="P2", type="plane")
    assert mock_fusion.last_request["method"] == "rename_construction"
    
    await delete_construction(name="P2", type="plane")
    assert mock_fusion.last_request["method"] == "delete_construction"

@pytest.mark.asyncio
async def test_parameter_management(mock_fusion):
    await delete_user_parameter(name="param1")
    assert mock_fusion.last_request["method"] == "delete_user_parameter"
