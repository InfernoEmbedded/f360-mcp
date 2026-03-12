import pytest
import os
from f360_mcp_server.server import undo, redo, save_design, capture_screenshot

@pytest.mark.asyncio
async def test_undo_redo(mock_fusion):
    res_undo = await undo(steps=1)
    assert "Undid 1 steps" in res_undo["message"]
    
    res_redo = await redo(steps=1)
    assert "Redid 1 steps" in res_redo["message"]

@pytest.mark.asyncio
async def test_save_design(mock_fusion):
    result = await save_design(description="Test save")
    assert "Design saved successfully" in result["message"]

@pytest.mark.asyncio
async def test_capture_screenshot(mock_fusion, tmp_path):
    # Absolute path on the "Fusion machine" (mocked)
    fusion_path = "/tmp/fusion_shot.png"
    # Local path on the "MCP machine"
    local_path = str(tmp_path / "local_shot.png")
    
    result = await capture_screenshot(
        file_path=fusion_path,
        send_to_mcp=True,
        local_file_path=local_path
    )
    
    assert "Screenshot saved" in result["message"]
    assert "local_file_path" in result
    assert os.path.exists(local_path)
    
    # Check if file is not empty (mock returns a 1x1 png base64)
    assert os.path.getsize(local_path) > 0
