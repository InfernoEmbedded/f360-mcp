import pytest
from server import (
    create_extrude, create_revolve, create_sweep, create_loft,
    create_hole, create_shell, create_fillet, create_chamfer,
    combine_bodies, feature_mirror
)

@pytest.mark.asyncio
async def test_create_extrude(mock_fusion):
    result = await create_extrude(sketch_name="Sketch 1", distance=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_extrude"

@pytest.mark.asyncio
async def test_create_revolve(mock_fusion):
    result = await create_revolve(sketch_name="Sketch 1", axis_ent_type="line", axis_ent_idx=0, angle=3.14)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_revolve"

@pytest.mark.asyncio
async def test_create_sweep(mock_fusion):
    result = await create_sweep(profile_sketch_name="S1", path_sketch_name="S2", path_ent_type="line", path_ent_idx=0)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_sweep"

@pytest.mark.asyncio
async def test_create_loft(mock_fusion):
    result = await create_loft(profiles_info=[{"sketch_name": "S1"}, {"sketch_name": "S2"}])
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_loft"

@pytest.mark.asyncio
async def test_create_hole(mock_fusion):
    result = await create_hole(sketch_name="S1", point_idx=0, diameter=1, depth=2)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_hole"

@pytest.mark.asyncio
async def test_create_shell(mock_fusion):
    result = await create_shell(body_name="Body 1", thickness=0.2)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_shell"

@pytest.mark.asyncio
async def test_create_fillet(mock_fusion):
    result = await create_fillet(body_name="Body 1", radius=0.5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_fillet"

@pytest.mark.asyncio
async def test_create_chamfer(mock_fusion):
    result = await create_chamfer(body_name="Body 1", distance=0.5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_chamfer"

@pytest.mark.asyncio
async def test_combine_bodies(mock_fusion):
    result = await combine_bodies(target_body_name="Body 1", tool_body_names=["Body 2"], operation="join")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "combine_bodies"

@pytest.mark.asyncio
async def test_feature_mirror(mock_fusion):
    result = await feature_mirror(body_name="Body 1", plane_name="XY")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "feature_mirror"
