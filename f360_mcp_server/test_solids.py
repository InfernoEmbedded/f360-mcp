import pytest
import json
from test_utils import compare_command_logs
from server import (
    create_extrude, create_revolve, create_sweep, create_loft,
    create_hole, create_shell, create_fillet, create_chamfer,
    combine_bodies, feature_mirror, split_body, scale_body,
    create_thread, move_body, measure_interference,
    create_rib, create_web, create_emboss,
    import_mesh, convert_mesh_to_solid, reload_addin
)

@pytest.mark.asyncio
async def test_create_extrude(mock_fusion, recorded_commands):
    # 1. Create extrude
    result = await create_extrude(
        name="TestExtrude",
        sketch_name="TestSketch",
        distance=5.0,
        operation="new_body"
    )
    assert "Successfully" in result["message"]
    assert result["feature_name"] == "TestExtrude"

    # 2. Check stability
    compare_command_logs("test_create_extrude", recorded_commands)

@pytest.mark.asyncio
async def test_create_revolve(mock_fusion):
    result = await create_revolve(name="TestRevolve", sketch_name="Sketch 1", axis_ent_type="line", axis_ent_idx=0, angle=3.14)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_revolve"

@pytest.mark.asyncio
async def test_create_sweep(mock_fusion):
    result = await create_sweep(name="TestSweep", profile_sketch_name="S1", path_sketch_name="S2", path_ent_type="line", path_ent_idx=0)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_sweep"

@pytest.mark.asyncio
async def test_create_loft(mock_fusion):
    result = await create_loft(name="TestLoft", profiles_info=[{"sketch_name": "S1"}, {"sketch_name": "S2"}])
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_loft"

@pytest.mark.asyncio
async def test_create_hole(mock_fusion):
    result = await create_hole(name="TestHole", sketch_name="S1", point_idx=0, diameter=1, depth=2)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_hole"

@pytest.mark.asyncio
async def test_create_shell(mock_fusion):
    result = await create_shell(name="TestShell", body_name="Body 1", thickness=0.2)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_shell"

@pytest.mark.asyncio
async def test_create_fillet(mock_fusion):
    result = await create_fillet(name="TestFillet", body_name="Body 1", radius=0.5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_fillet"

@pytest.mark.asyncio
async def test_create_chamfer(mock_fusion):
    result = await create_chamfer(name="TestChamfer", body_name="Body 1", distance=0.5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_chamfer"

@pytest.mark.asyncio
async def test_combine_bodies(mock_fusion):
    result = await combine_bodies(name="TestCombine", target_body_name="Body 1", tool_body_names=["Body 2"], operation="join")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "combine_bodies"

@pytest.mark.asyncio
async def test_feature_mirror(mock_fusion):
    result = await feature_mirror(name="TestMirror", body_name="Body 1", plane_name="XY")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "feature_mirror"

@pytest.mark.asyncio
async def test_split_body(mock_fusion):
    result = await split_body(name="TestSplit", body_name="Body 1", split_tool_name="XY")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "split_body"

@pytest.mark.asyncio
async def test_scale_body(mock_fusion):
    result = await scale_body(name="TestScale", body_name="Body 1", scale_factor=1.05)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "scale_body"

@pytest.mark.asyncio
async def test_create_thread(mock_fusion):
    result = await create_thread(name="TestThread", body_name="Body 1", face_index=0, is_modeled=True)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_thread"

@pytest.mark.asyncio
async def test_move_body(mock_fusion):
    result = await move_body(name="TestMove", body_name="Body 1", dx=1.0, dy=0.0, dz=5.0)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "move_body"

@pytest.mark.asyncio
async def test_measure_interference(mock_fusion):
    result = await measure_interference(body_names=["Body 1", "Body 2"])
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "measure_interference"

@pytest.mark.asyncio
async def test_create_rib(mock_fusion):
    result = await create_rib(name="TestRib", sketch_name="S1", thickness=0.1)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_rib"

@pytest.mark.asyncio
async def test_create_web(mock_fusion):
    result = await create_web(name="TestWeb", sketch_name="S1", thickness=0.1)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_web"

@pytest.mark.asyncio
async def test_create_emboss(mock_fusion):
    result = await create_emboss(name="TestEmboss", sketch_name="S1", body_name="Body 1", depth=0.2)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_emboss"

@pytest.mark.anyio
async def test_import_mesh(mock_fusion):
    result = await import_mesh(file_path="/tmp/test.stl")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "import_mesh"

@pytest.mark.asyncio
async def test_convert_mesh_to_solid(mock_fusion):
    result = await convert_mesh_to_solid(name="TestConvert", body_name="Mesh 1")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "convert_mesh_to_solid"

@pytest.mark.anyio
async def test_reload_addin(mock_fusion):
    result = await reload_addin()
    assert "Reloader script executed" in result["message"]
    assert mock_fusion.last_request["method"] == "reload_addin"
