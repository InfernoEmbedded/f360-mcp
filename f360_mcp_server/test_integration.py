import pytest
import os
import shutil
from server import export_model, execute_script, compute_all, get_design_health

@pytest.mark.asyncio
async def test_export_model_mcp(mock_fusion, tmp_path):
    # Test exporting and sending to MCP
    local_path = tmp_path / "test_export.stl"
    result = await export_model(
        file_path="/tmp/f360_export.stl",
        send_to_mcp=True,
        local_file_path=str(local_path)
    )
    assert "Successfully" in result["message"]
    assert os.path.exists(local_path)
    with open(local_path, "rb") as f:
        assert f.read() == b"dummy_stl_content"

@pytest.mark.asyncio
async def test_execute_script(mock_fusion):
    script = "print('hello')"
    result = await execute_script(script_code=script)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "execute_script"
    assert mock_fusion.last_request["params"]["script_code"] == script

@pytest.mark.asyncio
async def test_health_tools(mock_fusion):
    result = await get_design_health()
    assert "healthy" in result["message"]
    assert mock_fusion.last_request["method"] == "get_design_health"
    
    result = await compute_all()
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "compute_all"
