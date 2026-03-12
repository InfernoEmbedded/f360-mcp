import pytest
from server import (
    create_sketch, add_circle, add_line, add_rectangle, 
    add_arc, add_spline, add_polygon, add_ellipse, add_point, add_text
)

@pytest.mark.asyncio
async def test_create_sketch(mock_fusion):
    result = await create_sketch(plane_name="XY")
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "create_sketch"
    assert mock_fusion.last_request["params"]["plane_name"] == "XY"

@pytest.mark.asyncio
async def test_add_circle(mock_fusion):
    result = await add_circle(sketch_name="TestSketch", x=0, y=0, radius=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_circle"
    assert mock_fusion.last_request["params"]["radius"] == 5

@pytest.mark.asyncio
async def test_add_line(mock_fusion):
    result = await add_line(sketch_name="TestSketch", x1=0, y1=0, x2=10, y2=10)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_line"
    assert mock_fusion.last_request["params"]["x2"] == 10

@pytest.mark.asyncio
async def test_add_rectangle(mock_fusion):
    result = await add_rectangle(sketch_name="TestSketch", x1=0, y1=0, x2=10, y2=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_rectangle"
    assert mock_fusion.last_request["params"]["x2"] == 10

@pytest.mark.asyncio
async def test_add_arc(mock_fusion):
    result = await add_arc(sketch_name="TestSketch", x1=0, y1=0, x2=5, y2=5, x3=10, y3=0)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_arc"

@pytest.mark.asyncio
async def test_add_spline(mock_fusion):
    result = await add_spline(sketch_name="TestSketch", points=[[0,0], [1,1], [2,0]])
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_spline"

@pytest.mark.asyncio
async def test_add_polygon(mock_fusion):
    result = await add_polygon(sketch_name="TestSketch", center_x=0, center_y=0, num_sides=6, vertex_x=5, vertex_y=0)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_polygon"

@pytest.mark.asyncio
async def test_add_ellipse(mock_fusion):
    result = await add_ellipse(sketch_name="TestSketch", center_x=0, center_y=0, major_x=10, major_y=0, minor_x=0, minor_y=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_ellipse"

@pytest.mark.asyncio
async def test_add_point(mock_fusion):
    result = await add_point(sketch_name="TestSketch", x=5, y=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_point"

@pytest.mark.asyncio
async def test_add_text(mock_fusion):
    result = await add_text(sketch_name="TestSketch", text="Hello", x=0, y=0)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_text"

from server import (
    apply_constraint, add_symmetry_constraint, add_distance_dimension,
    add_radial_dimension, add_diameter_dimension, add_angular_dimension
)

@pytest.mark.asyncio
async def test_apply_constraint(mock_fusion):
    result = await apply_constraint(sketch_name="TestSketch", constraint_type="parallel", ent1_type="line", ent1_idx=0, ent2_type="line", ent2_idx=1)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "apply_constraint"

@pytest.mark.asyncio
async def test_add_symmetry_constraint(mock_fusion):
    result = await add_symmetry_constraint(sketch_name="TestSketch", ent1_type="line", ent1_idx=0, ent2_type="line", ent2_idx=1, sym_line_type="line", sym_line_idx=2)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_symmetry_constraint"

@pytest.mark.asyncio
async def test_add_distance_dimension(mock_fusion):
    result = await add_distance_dimension(sketch_name="TestSketch", ent1_type="line", ent1_idx=0, ent2_type="line", ent2_idx=1, text_x=5, text_y=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_distance_dimension"

@pytest.mark.asyncio
async def test_add_radial_dimension(mock_fusion):
    result = await add_radial_dimension(sketch_name="TestSketch", ent_type="arc", ent_idx=0, text_x=5, text_y=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_radial_dimension"

@pytest.mark.asyncio
async def test_add_diameter_dimension(mock_fusion):
    result = await add_diameter_dimension(sketch_name="TestSketch", ent_type="circle", ent_idx=0, text_x=5, text_y=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_diameter_dimension"

@pytest.mark.asyncio
async def test_add_angular_dimension(mock_fusion):
    result = await add_angular_dimension(sketch_name="TestSketch", line1_idx=0, line2_idx=1, text_x=5, text_y=5)
    assert "Successfully" in result["message"]
    assert mock_fusion.last_request["method"] == "add_angular_dimension"

