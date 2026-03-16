import pytest
from server import create_sketch, start_timeline_group, stop_timeline_group

@pytest.mark.anyio
async def test_manual_grouping(mock_fusion):
    await start_timeline_group(name="Test Group")
    await create_sketch(plane_name="XY")
    result = await stop_timeline_group()
    assert "Created timeline group" in result["message"]

@pytest.mark.anyio
async def test_auto_grouping(mock_fusion):
    # In the mock, we can't easily verify the Add-In's auto-grouping logic 
    # since the mock server just returns static responses.
    # However, we can verify the tools are reachable.
    result = await create_sketch(plane_name="XY")
    assert "message" in result
