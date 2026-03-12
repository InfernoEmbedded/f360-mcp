import pytest
import os
import shutil
import server

@pytest.mark.asyncio
async def test_export_model_mcp(mock_fusion, tmp_path):
    # Test exporting and sending to MCP
    local_path = tmp_path / "test_export.stl"
    result = await server.export_model(
        file_path="/tmp/f360_export.stl",
        send_to_mcp=True,
        local_file_path=str(local_path)
    )
    assert "success" in result["message"].lower()
    assert os.path.exists(local_path)
    with open(local_path, "rb") as f:
        assert f.read() == b"dummy_stl_content"

@pytest.mark.asyncio
async def test_execute_script(mock_fusion):
    script = "print('hello')"
    result = await server.execute_script(script_code=script)
    assert "success" in result["message"].lower()
    assert mock_fusion.last_request["method"] == "execute_script"
    assert mock_fusion.last_request["params"]["script_code"] == script

@pytest.mark.asyncio
async def test_health_tools(mock_fusion):
    result = await server.get_design_health()
    assert "healthy" in result["message"]
    assert mock_fusion.last_request["method"] == "get_design_health"
    
    result = await server.compute_all()
    assert "success" in result["message"].lower()
    assert mock_fusion.last_request["method"] == "compute_all"
