import pytest
import os
from f360_mcp_server.server import undo, redo, save_design, capture_screenshot

@pytest.mark.anyio
async def test_undo_redo(mock_fusion, recorded_commands):
    await undo(steps=1)
    await redo(steps=1)
    from test_utils import compare_command_logs
    compare_command_logs("test_undo_redo", recorded_commands)

@pytest.mark.anyio
async def test_save_design(mock_fusion, recorded_commands):
    await save_design(description="Test save")
    from test_utils import compare_command_logs
    compare_command_logs("test_save_design", recorded_commands)

@pytest.mark.anyio
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
