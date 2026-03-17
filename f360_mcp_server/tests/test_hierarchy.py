import pytest
from f360_mcp_server.server import initialize_tools, get_object_hierarchy

@pytest.mark.asyncio
async def test_get_object_hierarchy(mock_fusion):
    # Ensure tools are initialized (conftest does it, but we might need a refresh to pick up the new metadata)
    await initialize_tools()
    
    # Call the new tool
    result = await get_object_hierarchy()
    
    assert "hierarchy" in result
    hierarchy = result["hierarchy"]
    
    assert hierarchy["name"] == "Root"
    assert hierarchy["type"] == "Component"
    assert "bodies" in hierarchy
    assert hierarchy["bodies"][0]["name"] == "Body 1"
    assert hierarchy["bodies"][0]["type"] == "BRepBody"
    
    # Check children
    assert "children" in hierarchy
    child = hierarchy["children"][0]
    assert child["name"] == "Component 1"
    assert child["occurrence"] == "Component 1:1"
    assert child["bodies"][0]["name"] == "Body 1"
