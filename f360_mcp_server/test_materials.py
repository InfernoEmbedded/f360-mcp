import pytest
from server import list_materials, apply_material, list_appearances, apply_appearance

@pytest.mark.asyncio
async def test_list_materials(mock_fusion):
    result = await list_materials()
    assert "materials" in result
    assert len(result["materials"]) > 0
    assert result["materials"][0]["name"] == "Steel"
    assert mock_fusion.last_request["method"] == "list_materials"

@pytest.mark.asyncio
async def test_apply_material(mock_fusion):
    result = await apply_material(body_name="Body 1", material_name="Steel")
    assert "Successfully" in result["message"]
    assert "Steel" in result["message"]
    assert mock_fusion.last_request["method"] == "apply_material"
    assert mock_fusion.last_request["params"]["material_name"] == "Steel"

@pytest.mark.asyncio
async def test_list_appearances(mock_fusion):
    result = await list_appearances()
    assert "appearances" in result
    assert len(result["appearances"]) > 0
    assert result["appearances"][0]["name"] == "Paint - Red"
    assert mock_fusion.last_request["method"] == "list_appearances"

@pytest.mark.asyncio
async def test_apply_appearance(mock_fusion):
    result = await apply_appearance(body_name="Body 1", appearance_name="Chrome")
    assert "Successfully" in result["message"]
    assert "Chrome" in result["message"]
    assert mock_fusion.last_request["method"] == "apply_appearance"
    assert mock_fusion.last_request["params"]["appearance_name"] == "Chrome"
