import pytest
import pytest_asyncio
from f360_mcp_server.server import get_face_info, get_edge_info, get_sketch_info, undo, redo, save_design

@pytest.mark.asyncio
async def test_get_face_info(mock_fusion):
    result = await get_face_info(body_name="Body 1")
    assert result["body_name"] == "Body 1"
    assert len(result["faces"]) > 0
    assert result["faces"][0]["type"] == "Planar"

@pytest.mark.asyncio
async def test_get_edge_info(mock_fusion):
    result = await get_edge_info(body_name="Body 1")
    assert result["body_name"] == "Body 1"
    assert len(result["edges"]) > 0
    assert result["edges"][0]["type"] == "Line"

@pytest.mark.asyncio
async def test_get_sketch_info(mock_fusion):
    result = await get_sketch_info(sketch_name="Sketch 1")
    assert result["sketch_name"] == "Sketch 1"
    assert "profiles" in result
    assert result["curves_summary"][0]["count"] == 4

@pytest.mark.asyncio
async def test_undo_redo(mock_fusion):
    result_undo = await undo(steps=2)
    assert "Undid 2 steps" in result_undo["message"]
    
    result_redo = await redo(steps=1)
    assert "Redid 1 steps" in result_redo["message"]

@pytest.mark.asyncio
async def test_save_design(mock_fusion):
    result = await save_design(description="Test Save")
    assert "saved successfully" in result["message"]
