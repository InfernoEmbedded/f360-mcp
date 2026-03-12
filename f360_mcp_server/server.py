import argparse
import asyncio
import json
import os
import socket
import sys
import uuid
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

def get_addin_host():
    return os.environ.get('F360_ADDIN_HOST', '127.0.0.1')

def get_addin_port():
    return int(os.environ.get('F360_ADDIN_PORT', 30011))

mcp = FastMCP("fusion360-mcp")

@mcp.resource("cheat_sheet://main")
def get_cheat_sheet() -> str:
    """Returns the Fusion 360 MCP Cheat Sheet for LLMs."""
    path = os.path.join(os.path.dirname(__file__), "mcp_cheat_sheet.md")
    with open(path, "r") as f:
        return f.read()

async def send_to_addin(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(uuid.uuid4())
    }
    
    host = get_addin_host()
    port = get_addin_port()
    
    def sync_request():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0) # 5 second timeout for testing
                s.connect((host, port))
                s.sendall(json.dumps(request).encode('utf-8') + b'\n')
                
                # Read response
                buffer = ""
                while True:
                    data = s.recv(8192)
                    if not data:
                        break
                    buffer += data.decode('utf-8')
                    if '\n' in buffer:
                        break
                
                if not buffer.strip():
                    return {"error": "No response from Add-In"}
                
                return json.loads(buffer.strip())
        except Exception as e:
            return {"error": str(e)}

    try:
        response = await asyncio.to_thread(sync_request)
        
        # Check for errors returned by the Add-In or during socket communication
        if "error" in response:
            raise Exception(f"Fusion 360 Error: {response['error']}")
            
        return response.get("result", {})
    except ConnectionRefusedError:
        raise Exception(f"Could not connect to Fusion 360 Add-In at {host}:{port}. Is it running?")
    except json.JSONDecodeError:
        raise Exception("Invalid response from Fusion 360 Add-In.")

@mcp.tool()
async def create_sketch(
    plane_name: str = "XY",
    body_name: Optional[str] = None,
    face_index: Optional[int] = None
) -> Dict[str, Any]:
    """
    Creates a new sketch.
    
    To sketch on an origin plane or construction plane, use `plane_name` ("XY", "XZ", "YZ", or a plane's name).
    To sketch directly on a solid face, provide the `body_name` and the `face_index` (retrieve these using the `find_faces` tool).
    
    Returns the name of the newly created sketch, which is required for all drawing operations.
    """
    return await send_to_addin('create_sketch', {
        "plane_name": plane_name,
        "body_name": body_name,
        "face_index": face_index
    })

@mcp.tool()
async def add_circle(sketch_name: str, x: float, y: float, radius: float) -> Dict[str, Any]:
    """
    Adds a circle to an existing sketch.
    
    Arguments:
    - sketch_name: The name of the target sketch.
    - x, y: Center point coordinates in centimeters (cm) relative to the sketch origin.
    - radius: Radius of the circle in centimeters (cm).
    """
    return await send_to_addin('add_circle', {
        "sketch_name": sketch_name,
        "x": x,
        "y": y,
        "radius": radius
    })

@mcp.tool()
async def add_line(sketch_name: str, x1: float, y1: float, x2: float, y2: float) -> Dict[str, Any]:
    """
    Adds a line to an existing sketch.
    
    Arguments:
    - sketch_name: The name of the target sketch.
    - x1, y1: Start point coordinates in centimeters (cm).
    - x2, y2: End point coordinates in centimeters (cm).
    """
    return await send_to_addin('add_line', {
        "sketch_name": sketch_name,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2
    })

@mcp.tool()
async def add_rectangle(
    sketch_name: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float | None = None,
    y3: float | None = None,
    rect_type: str = "two_point"
) -> Dict[str, Any]:
    """
    Adds a rectangle to an existing sketch.
    
    Types:
    - "two_point" (default): (x1,y1) and (x2,y2) are opposite corners.
    - "three_point": (x1,y1), (x2,y2) define the first side, (x3,y3) defines the depth.
    - "center": (x1,y1) is the center point, (x2,y2) is one corner.
    
    All coordinates are in centimeters (cm).
    """
    params = {
        "sketch_name": sketch_name,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "rect_type": rect_type
    }
    if x3 is not None: params["x3"] = x3
    if y3 is not None: params["y3"] = y3
    return await send_to_addin('add_rectangle', params)

@mcp.tool()
async def add_arc(
    sketch_name: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float = 0,
    arc_type: str = "three_point"
) -> Dict[str, Any]:
    """
    Adds an arc to an existing sketch.
    
    Types:
    - "three_point" (default): (x1,y1) is start, (x2,y2) is a point on the arc, (x3,y3) is the end.
    - "center_start_sweep": (x1,y1) is the center point, (x2,y2) is the start point, x3 is the sweep angle in DEGREES.
    
    Coordinates are in centimeters (cm).
    """
    return await send_to_addin('add_arc', {
        "sketch_name": sketch_name,
        "x1": x1, "y1": y1,
        "x2": x2, "y2": y2,
        "x3": x3, "y3": y3,
        "arc_type": arc_type
    })

@mcp.tool()
async def add_spline(sketch_name: str, points: list[list[float]]) -> Dict[str, Any]:
    """
    Adds a fitted spline (smooth curve) through a list of points.
    
    Arguments:
    - sketch_name: Target sketch name.
    - points: A list of [x, y] coordinate pairs in cm, e.g., [[0,0], [2,5], [5,0]].
    """
    return await send_to_addin('add_spline', {
        "sketch_name": sketch_name,
        "points": points
    })

@mcp.tool()
async def add_polygon(
    sketch_name: str,
    center_x: float,
    center_y: float,
    num_sides: int,
    vertex_x: float,
    vertex_y: float,
    poly_type: str = "inscribed"
) -> Dict[str, Any]:
    """
    Adds a regular polygon to a sketch.
    
    Arguments:
    - center_x, center_y: Center of the polygon (cm).
    - num_sides: Number of sides (e.g., 6 for a hexagon).
    - vertex_x, vertex_y: Coordinates of one vertex to define size and orientation (cm).
    - poly_type: "inscribed" (corners touch circle) or "circumscribed" (sides touch circle).
    """
    return await send_to_addin('add_polygon', {
        "sketch_name": sketch_name,
        "center_x": center_x,
        "center_y": center_y,
        "num_sides": num_sides,
        "vertex_x": vertex_x,
        "vertex_y": vertex_y,
        "poly_type": poly_type
    })

@mcp.tool()
async def add_ellipse(
    sketch_name: str,
    center_x: float,
    center_y: float,
    major_x: float,
    major_y: float,
    minor_x: float,
    minor_y: float
) -> Dict[str, Any]:
    """
    Adds an ellipse to a sketch.
    
    Arguments:
    - center_x, center_y: Center point (cm).
    - major_x, major_y: Coordinates defining the end of the major axis (cm).
    - minor_x, minor_y: Coordinates defining the end of the minor axis (cm).
    """
    return await send_to_addin('add_ellipse', {
        "sketch_name": sketch_name,
        "center_x": center_x, "center_y": center_y,
        "major_x": major_x, "major_y": major_y,
        "minor_x": minor_x, "minor_y": minor_y
    })

@mcp.tool()
async def add_point(sketch_name: str, x: float, y: float) -> Dict[str, Any]:
    """Adds a point to a sketch."""
    return await send_to_addin('add_point', {"sketch_name": sketch_name, "x": x, "y": y})

@mcp.tool()
async def add_text(sketch_name: str, text: str, x: float, y: float, height: float = 0.5) -> Dict[str, Any]:
    """Adds text to a sketch at the specified (x, y) location."""
    return await send_to_addin('add_text', {
        "sketch_name": sketch_name,
        "text": text,
        "x": x,
        "y": y,
        "height": height
    })

@mcp.tool()
async def apply_constraint(
    sketch_name: str,
    constraint_type: str,
    ent1_type: str,
    ent1_idx: int,
    ent2_type: str | None = None,
    ent2_idx: int | None = None
) -> Dict[str, Any]:
    """
    Applies a geometric constraint between sketch entities.
    
    Constraint Types:
    - "coincident", "collinear", "concentric", "midpoint", "parallel", "perpendicular", "horizontal", "vertical", "tangent", "equal".
    
    Entity Types:
    - "line", "line_start", "line_end", "circle", "circle_center", "arc", "arc_start", "arc_end", "arc_center", "point".
    
    Indices:
    - 0-based index of that geometry type as created in the specific sketch. Use `get_sketch_info` to find counts if needed.
    """
    params = {
        "sketch_name": sketch_name,
        "constraint_type": constraint_type,
        "ent1_type": ent1_type,
        "ent1_idx": ent1_idx
    }
    if ent2_type is not None and ent2_idx is not None:
        params["ent2_type"] = ent2_type
        params["ent2_idx"] = ent2_idx
        
    return await send_to_addin('apply_constraint', params)

@mcp.tool()
async def add_symmetry_constraint(
    sketch_name: str,
    ent1_type: str,
    ent1_idx: int,
    ent2_type: str,
    ent2_idx: int,
    sym_line_type: str,
    sym_line_idx: int
) -> Dict[str, Any]:
    """
    Applies a symmetry constraint between two sketch entities across a symmetry line.
    """
    return await send_to_addin('add_symmetry_constraint', {
        "sketch_name": sketch_name,
        "ent1_type": ent1_type,
        "ent1_idx": ent1_idx,
        "ent2_type": ent2_type,
        "ent2_idx": ent2_idx,
        "sym_line_type": sym_line_type,
        "sym_line_idx": sym_line_idx
    })

@mcp.tool()
async def add_distance_dimension(
    sketch_name: str,
    ent1_type: str,
    ent1_idx: int,
    ent2_type: str,
    ent2_idx: int,
    text_x: float,
    text_y: float,
    orientation: str = "aligned"
) -> Dict[str, Any]:
    """
    Adds a linear distance dimension between two entities.
    
    Arguments:
    - sketch_name: Target sketch name.
    - ent1_idx, ent2_idx: Indices of entities (lines, points, etc.) in the sketch.
    - text_x, text_y: Coordinates for placing the dimension text (cm).
    - orientation: "aligned", "horizontal", or "vertical".
    """
    return await send_to_addin('add_distance_dimension', {
        "sketch_name": sketch_name,
        "ent1_type": ent1_type,
        "ent1_idx": ent1_idx,
        "ent2_type": ent2_type,
        "ent2_idx": ent2_idx,
        "text_x": text_x,
        "text_y": text_y,
        "orientation": orientation
    })

@mcp.tool()
async def add_radial_dimension(
    sketch_name: str,
    ent_type: str,
    ent_idx: int,
    text_x: float,
    text_y: float
) -> Dict[str, Any]:
    """Adds a radial dimension (cm) to an arc or circle in a sketch."""
    return await send_to_addin('add_radial_dimension', {
        "sketch_name": sketch_name,
        "ent_type": ent_type,
        "ent_idx": ent_idx,
        "text_x": text_x,
        "text_y": text_y
    })

@mcp.tool()
async def add_diameter_dimension(
    sketch_name: str,
    ent_type: str,
    ent_idx: int,
    text_x: float,
    text_y: float
) -> Dict[str, Any]:
    """Adds a diameter dimension (cm) to a circle or arc in a sketch."""
    return await send_to_addin('add_diameter_dimension', {
        "sketch_name": sketch_name,
        "ent_type": ent_type,
        "ent_idx": ent_idx,
        "text_x": text_x,
        "text_y": text_y
    })

@mcp.tool()
async def add_angular_dimension(
    sketch_name: str,
    line1_idx: int,
    line2_idx: int,
    text_x: float,
    text_y: float
) -> Dict[str, Any]:
    """Adds an angular dimension between two lines."""
    return await send_to_addin('add_angular_dimension', {
        "sketch_name": sketch_name,
        "line1_idx": line1_idx,
        "line2_idx": line2_idx,
        "text_x": text_x,
        "text_y": text_y
    })

@mcp.tool()
async def list_sketches() -> Dict[str, Any]:
    """Lists all sketches in the active design."""
    return await send_to_addin('list_sketches', {})

@mcp.tool()
async def delete_sketch(sketch_name: str) -> Dict[str, Any]:
    """Deletes a sketch by name."""
    return await send_to_addin('delete_sketch', {"sketch_name": sketch_name})

@mcp.tool()
async def project_geometry(
    sketch_name: str,
    ent_type: str,
    ent_idx: int,
    from_sketch_name: str = None
) -> Dict[str, Any]:
    """
    Projects geometry from another sketch into the active sketch.
    If from_sketch_name is omitted, it attempts to resolve the entity from the active sketch
    (or another active context if valid).
    """
    params = {
        "sketch_name": sketch_name,
        "ent_type": ent_type,
        "ent_idx": ent_idx
    }
    if from_sketch_name:
        params["from_sketch_name"] = from_sketch_name
    return await send_to_addin('project_geometry', params)

@mcp.tool()
async def offset_geometry(
    sketch_name: str,
    ent_type: str,
    ent_idx: int,
    offset_distance: float
) -> Dict[str, Any]:
    """
    Creates an offset of a sketch entity.
    
    Arguments:
    - offset_distance: Distance in cm. Positive offsets away from center (for closed loops); negative offsets inward.
    """
    return await send_to_addin('offset_geometry', {
        "sketch_name": sketch_name,
        "ent_type": ent_type,
        "ent_idx": ent_idx,
        "offset_distance": offset_distance
    })

@mcp.tool()
async def delete_sketch_entity(
    sketch_name: str,
    ent_type: str,
    ent_idx: int
) -> Dict[str, Any]:
    """Deletes a specific entity from a sketch by its type and index."""
    return await send_to_addin('delete_sketch_entity', {
        "sketch_name": sketch_name,
        "ent_type": ent_type,
        "ent_idx": ent_idx
    })

@mcp.tool()
async def trim_sketch_geometry(
    sketch_name: str,
    ent_type: str,
    ent_idx: int,
    x: float,
    y: float
) -> Dict[str, Any]:
    """
    Trims a sketch curve around the provided (x, y) coordinates.
    """
    return await send_to_addin('trim_sketch_geometry', {
        "sketch_name": sketch_name,
        "ent_type": ent_type,
        "ent_idx": ent_idx,
        "x": x,
        "y": y
    })

@mcp.tool()
async def create_extrude(
    sketch_name: str,
    distance: float,
    operation: str = "new_body",
    profile_index: int = 0
) -> Dict[str, Any]:
    """
    Extrudes a sketch profile to create 3D volume.
    
    Arguments:
    - distance: Extrusion depth in cm.
    - operation: 'new_body', 'join', 'cut', or 'intersect'.
    - profile_index: Index of the closed profile to extrude (0 is usually the main sketch loop).
    """
    return await send_to_addin('create_extrude', {
        "sketch_name": sketch_name,
        "distance": distance,
        "operation": operation,
        "profile_index": profile_index
    })

@mcp.tool()
async def create_revolve(
    sketch_name: str,
    axis_ent_type: str,
    axis_ent_idx: int,
    angle: float,
    operation: str = "new_body",
    profile_index: int = 0
) -> Dict[str, Any]:
    """
    Revolves a profile around an axis to create a 3D volume.
    
    Arguments:
    - axis_ent_type: Typically "line" from the same sketch.
    - angle: Revolve angle in DEGREES (e.g., 360 for full revolve).
    - operation: 'new_body', 'join', 'cut', or 'intersect'.
    """
    return await send_to_addin('create_revolve', {
        "sketch_name": sketch_name,
        "axis_ent_type": axis_ent_type,
        "axis_ent_idx": axis_ent_idx,
        "angle": angle,
        "operation": operation,
        "profile_index": profile_index
    })

@mcp.tool()
async def create_sweep(
    profile_sketch_name: str,
    path_sketch_name: str,
    path_ent_type: str,
    path_ent_idx: int,
    operation: str = "new_body",
    profile_index: int = 0
) -> Dict[str, Any]:
    """
    Sweeps a specific closed profile along a path entity (like a line or spline).
    operation can be 'new_body', 'join', 'cut', or 'intersect'.
    """
    return await send_to_addin('create_sweep', {
        "profile_sketch_name": profile_sketch_name,
        "path_sketch_name": path_sketch_name,
        "path_ent_type": path_ent_type,
        "path_ent_idx": path_ent_idx,
        "operation": operation,
        "profile_index": profile_index
    })

@mcp.tool()
async def list_bodies() -> Dict[str, Any]:
    """Lists all bodies in the active design."""
    return await send_to_addin('list_bodies', {})

@mcp.tool()
async def combine_bodies(
    target_body_name: str,
    tool_body_names: list[str],
    operation: str = "join"
) -> Dict[str, Any]:
    """
    Combines or subtracts bodies.
    
    Arguments:
    - operation: 'join' (fuse), 'cut' (boolean subtract), or 'intersect'.
    """
    return await send_to_addin('combine_bodies', {
        "target_body_name": target_body_name,
        "tool_body_names": tool_body_names,
        "operation": operation
    })

@mcp.tool()
async def create_hole(
    sketch_name: str,
    point_idx: int,
    diameter: float,
    depth: float
) -> Dict[str, Any]:
    """
    Creates a simple circular hole at a sketch point.
    
    Arguments:
    - diameter, depth: Dimensions in centimeters (cm).
    """
    return await send_to_addin('create_hole', {
        "sketch_name": sketch_name,
        "point_idx": point_idx,
        "diameter": diameter,
        "depth": depth
    })

@mcp.tool()
async def create_shell(
    body_name: str,
    thickness: float
) -> Dict[str, Any]:
    """
    Hollows out a specified solid body.
    
    Arguments:
    - thickness: Wall thickness in centimeters (cm).
    """
    return await send_to_addin('create_shell', {
        "body_name": body_name,
        "thickness": thickness
    })

@mcp.tool()
async def create_fillet(
    body_name: str,
    radius: float
) -> Dict[str, Any]:
    """
    Fillets all edges of a specified body.
    
    Arguments:
    - radius: Fillet radius in centimeters (cm).
    """
    return await send_to_addin('create_fillet', {
        "body_name": body_name,
        "radius": radius
    })

@mcp.tool()
async def create_chamfer(
    body_name: str,
    distance: float
) -> Dict[str, Any]:
    """
    Chamfers all edges of a specified body.
    
    Arguments:
    - distance: Chamfer distance in centimeters (cm).
    """
    return await send_to_addin('create_chamfer', {
        "body_name": body_name,
        "distance": distance
    })

@mcp.tool()
async def feature_mirror(
    body_name: str,
    plane_name: str
) -> Dict[str, Any]:
    """
    Mirrors a specified body across an origin plane.
    Allowed plane names: 'xy', 'yz', 'xz'.
    """
    return await send_to_addin('feature_mirror', {
        "body_name": body_name,
        "plane_name": plane_name
    })

@mcp.tool()
async def create_loft(
    profiles_info: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Creates a loft feature by blending between multiple sketch profiles.
    
    Arguments:
    - profiles_info: List of profiles, e.g., [{"sketch_name": "sk1", "profile_idx": 0}, {"sketch_name": "sk2", "profile_idx": 0}].
    """
    return await send_to_addin('create_loft', {
        "profiles_info": profiles_info
    })

@mcp.tool()
async def execute_script(
    script_code: str
) -> Dict[str, Any]:
    """
    Executes arbitrary Python code in the Fusion 360 environment.
    The code has access to the standard global variables: 'app' (adsk.core.Application.get()), 'ui', and 'adsk'.
    If the script needs to return a value, it must assign it to a global variable named 'result'.
    Example: 
    ```python
    design = app.activeProduct
    result = {"design_name": design.parentDocument.name}
    ```
    """
    return await send_to_addin('execute_script', {
        "script_code": script_code
    })

@mcp.tool()
async def create_offset_plane(
    base_plane: str,
    offset: float
) -> Dict[str, Any]:
    """
    Creates a new construction plane offset from a base.
    
    Arguments:
    - base_plane: "XY", "YZ", "XZ", or the name of an existing construction plane.
    - offset: Distance in centimeters (cm).
    """
    return await send_to_addin('create_offset_plane', {
        "base_plane": base_plane,
        "offset": offset
    })

@mcp.tool()
async def create_plane_at_angle(
    axis_name: str,
    angle_deg: float
) -> Dict[str, Any]:
    """
    Creates a new construction plane at an angle relative to an axis.
    
    Arguments:
    - axis_name: "X", "Y", "Z", or the name of an existing construction axis.
    - angle_deg: Angle in DEGREES.
    """
    return await send_to_addin('create_plane_at_angle', {
        "axis_name": axis_name,
        "angle_deg": angle_deg
    })

@mcp.tool()
async def get_body_properties(
    body_name: str
) -> Dict[str, Any]:
    """
    Returns physical properties of a solid body (mass, volume, area, bounding box).
    Required for engineering calculations or measuring overall dimensions.
    """
    return await send_to_addin('get_body_properties', {
        "body_name": body_name
    })

@mcp.tool()
async def find_faces(
    body_name: str
) -> Dict[str, Any]:
    """
    Returns a list of faces on a body with their index, normals, center points, and area.
    Use this to look for faces to attach new sketches to.
    """
    return await send_to_addin('find_faces', {
        "body_name": body_name
    })

@mcp.tool()
async def create_user_parameter(
    name: str,
    expression: str,
    unit: str = "",
    description: str = ""
) -> Dict[str, Any]:
    """
    Creates a new user parametric parameter.
    
    Arguments:
    - expression: Math expression or value string (e.g., "50mm", "width * 2").
    - unit: Optional unit (e.g., "mm", "cm", "deg"). Default is cm if numeric only.
    - description: Optional comment for future reference.
    """
    return await send_to_addin('create_user_parameter', {
        "name": name,
        "expression": expression,
        "unit": unit,
        "comment": description
    })

@mcp.tool()
async def list_parameters() -> Dict[str, Any]:
    """
    Lists all parametric parameters (user and model) in the design.
    """
    return await send_to_addin('list_parameters', {})

@mcp.tool()
async def update_parameter(
    name: str,
    expression: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates an existing parameter's expression and/or description.
    Works for both user and model parameters.
    """
    return await send_to_addin('update_parameter', {
        "name": name,
        "expression": expression,
        "comment": description
    })

@mcp.tool()
async def create_component(name: str) -> Dict[str, Any]:
    """
    Creates a new empty sub-component in the design.
    """
    return await send_to_addin('create_component', {"name": name})

@mcp.tool()
async def create_rectangular_pattern(
    body_name: str,
    count_x: int,
    count_y: int,
    distance_x: float,
    distance_y: float
) -> Dict[str, Any]:
    """
    Patterns a solid body in a rectangular grid.
    
    Arguments:
    - distances: Spacings in centimeters (cm).
    """
    return await send_to_addin('create_rectangular_pattern', {
        "body_name": body_name,
        "count_x": count_x,
        "count_y": count_y,
        "distance_x": distance_x,
        "distance_y": distance_y
    })

@mcp.tool()
async def create_circular_pattern(
    body_name: str,
    axis_name: str,
    count: int,
    angle_deg: float
) -> Dict[str, Any]:
    """
    Creates a circular pattern of a solid body around an axis.
    axis_name can be "X", "Y", "Z". Angle is in degrees.
    """
    return await send_to_addin('create_circular_pattern', {
        "body_name": body_name,
        "axis_name": axis_name,
        "count": count,
        "angle_deg": angle_deg
    })

@mcp.tool()
async def export_model(
    file_path: str,
    file_type: str = "step",
    body_name: Optional[str] = None,
    send_to_mcp: bool = False,
    local_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exports the entire design or a specific body.
    file_path: The absolute path to save the file ON THE FUSION 360 MACHINE.
    file_type: "step", "stl", or "3mf".
    body_name: (optional) Name of a specific body to export.
    send_to_mcp: If True, the file is sent over the network.
    local_file_path: If send_to_mcp is True, the absolute path to save the file ON THE MCP HOST MACHINE.
    """
    if send_to_mcp and not local_file_path:
        raise Exception("local_file_path must be provided if send_to_mcp is True.")
        
    response = await send_to_addin('export_model', {
        "file_path": file_path,
        "file_type": file_type,
        "body_name": body_name,
        "send_to_mcp": send_to_mcp
    })
    
    if send_to_mcp and "file_content_base64" in response and isinstance(local_file_path, str):
        import base64
        import os
        
        local_dir = os.path.dirname(local_file_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
            
        with open(local_file_path, "wb") as f:
            f.write(base64.b64decode(response["file_content_base64"]))
            
        response["message"] = f"Successfully exported model and saved to MCP host at {local_file_path}"
        response.pop("file_content_base64", None)
        response["local_file_path"] = local_file_path
        
    return response

@mcp.tool()
async def rename_body(
    old_name: str,
    new_name: str
) -> Dict[str, Any]:
    """
    Renames a solid body in the design.
    """
    return await send_to_addin('rename_body', {
        "old_name": old_name,
        "new_name": new_name
    })

@mcp.tool()
async def list_features() -> Dict[str, Any]:
    """
    Lists all modeling features in the design timeline.
    """
    return await send_to_addin('list_features', {})

@mcp.tool()
async def rename_feature(
    old_name: str,
    new_name: str
) -> Dict[str, Any]:
    """
    Renames a feature in the design timeline.
    """
    return await send_to_addin('rename_feature', {
        "old_name": old_name,
        "new_name": new_name
    })

@mcp.tool()
async def rename_sketch(old_name: str, new_name: str) -> Dict[str, Any]:
    """Renames a sketch in the design."""
    return await send_to_addin('rename_sketch', {"old_name": old_name, "new_name": new_name})

@mcp.tool()
async def delete_body(body_name: str) -> Dict[str, Any]:
    """Deletes a solid body from the design."""
    return await send_to_addin('delete_body', {"body_name": body_name})

@mcp.tool()
async def delete_feature(feature_name: str) -> Dict[str, Any]:
    """Deletes a modeling feature from the timeline."""
    return await send_to_addin('delete_feature', {"feature_name": feature_name})

@mcp.tool()
async def list_components() -> Dict[str, Any]:
    """Lists all component instances (occurrences) in the design."""
    return await send_to_addin('list_components', {})

@mcp.tool()
async def rename_component(old_name: str, new_name: str) -> Dict[str, Any]:
    """Renames a component definition."""
    return await send_to_addin('rename_component', {"old_name": old_name, "new_name": new_name})

@mcp.tool()
async def delete_component(occurrence_name: str) -> Dict[str, Any]:
    """Deletes a component instance (occurrence) from the design."""
    return await send_to_addin('delete_component', {"occurrence_name": occurrence_name})

@mcp.tool()
async def list_construction() -> Dict[str, Any]:
    """Lists all construction planes, axes, and points."""
    return await send_to_addin('list_construction', {})

@mcp.tool()
async def rename_construction(old_name: str, new_name: str, type: str = "plane") -> Dict[str, Any]:
    """Renames a construction item. type: 'plane', 'axis', or 'point'."""
    return await send_to_addin('rename_construction', {"old_name": old_name, "new_name": new_name, "type": type})

@mcp.tool()
async def delete_construction(name: str, type: str = "plane") -> Dict[str, Any]:
    """Deletes a construction item. type: 'plane', 'axis', or 'point'."""
    return await send_to_addin('delete_construction', {"name": name, "type": type})

@mcp.tool()
async def delete_user_parameter(name: str) -> Dict[str, Any]:
    """Deletes a user parameter."""
    return await send_to_addin('delete_user_parameter', {"name": name})

@mcp.tool()
async def compute_all() -> Dict[str, Any]:
    """
    Triggers a full rebuild of the design (Compute All) and returns the health status.
    """
    return await send_to_addin('compute_all', {})

@mcp.tool()
async def get_design_health() -> Dict[str, Any]:
    """
    Checks the design timeline for any errors or warnings.
    """
    return await send_to_addin('get_design_health', {})

@mcp.tool()
async def list_materials() -> Dict[str, Any]:
    """
    Lists physical materials from the 'Fusion 360 Material Library' and 'Favorite' libraries.
    Returns names that can be used with `apply_material`.
    """
    return await send_to_addin('list_materials', {})

@mcp.tool()
async def apply_material(body_name: str, material_name: str) -> Dict[str, Any]:
    """
    Sets the physical material of a body.
    """
    return await send_to_addin('apply_material', {"body_name": body_name, "material_name": material_name})

@mcp.tool()
async def list_appearances() -> Dict[str, Any]:
    """
    Lists visual appearances from the libraries.
    Returns names that can be used with `apply_appearance`.
    """
    return await send_to_addin('list_appearances', {})

@mcp.tool()
async def apply_appearance(body_name: str, appearance_name: str) -> Dict[str, Any]:
    """
    Sets the visual appearance of a body.
    """
    return await send_to_addin('apply_appearance', {"body_name": body_name, "appearance_name": appearance_name})

@mcp.tool()
async def start_timeline_group(name: str) -> Dict[str, Any]:
    """
    Starts a timeline group. All operations until stop_timeline_group will be grouped.
    Use this to logically group related features (e.g., "Lid Features").
    """
    return await send_to_addin('start_timeline_group', {"name": name})

@mcp.tool()
async def stop_timeline_group() -> Dict[str, Any]:
    """
    Stops the current timeline group and creates it in Fusion 360.
    """
    return await send_to_addin('stop_timeline_group', {})

@mcp.tool()
async def get_face_info(body_name: str) -> Dict[str, Any]:
    """
    Returns indices and geometry data for ALL faces of a body.
    
    Use this to identify which face index (0-based) to use for `create_sketch`.
    Data includes: normal vector, center point (cm), and surface area (cm^2).
    """
    return await send_to_addin('get_face_info', {"body_name": body_name})

@mcp.tool()
async def get_edge_info(body_name: str) -> Dict[str, Any]:
    """
    Returns indices and lengths for ALL edges of a body.
    
    Use this to identify which edge index (0-based) to use for `create_fillet` or `create_chamfer`.
    Data includes: edge type and length in centimeters (cm).
    """
    return await send_to_addin('get_edge_info', {"body_name": body_name})

@mcp.tool()
async def get_sketch_info(sketch_name: str) -> Dict[str, Any]:
    """
    Returns detailed information about a sketch, including profiles and curve counts.
    """
    return await send_to_addin('get_sketch_info', {"sketch_name": sketch_name})

@mcp.tool()
async def undo(steps: int = 1) -> Dict[str, Any]:
    """Undoes the last action(s) in Fusion 360."""
    return await send_to_addin('undo', {"steps": steps})

@mcp.tool()
async def redo(steps: int = 1) -> Dict[str, Any]:
    """Redoes previously undone actions in Fusion 360."""
    return await send_to_addin('redo', {"steps": steps})

@mcp.tool()
async def save_design(description: str = "Saved via MCP") -> Dict[str, Any]:
    """Saves the current Fusion 360 design."""
    return await send_to_addin('save_design', {"description": description})

@mcp.tool()
async def create_joint(
    component1_name: str,
    component2_name: str,
    joint_type: str = "rigid",
    offset_x: float = 0,
    offset_y: float = 0,
    offset_z: float = 0
) -> Dict[str, Any]:
    """
    Creates a joint (mechanical connection) between two components.
    
    Arguments:
    - joint_type: "rigid" (fixed), "revolute" (rotational), or "slider" (linear).
    - offsets: Position offsets in centimeters (cm).
    """
    return await send_to_addin('create_joint', {
        "component1_name": component1_name,
        "component2_name": component2_name,
        "joint_type": joint_type,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "offset_z": offset_z
    })

@mcp.tool()
async def create_as_built_joint(
    component1_name: str,
    component2_name: str,
    joint_type: str = "rigid"
) -> Dict[str, Any]:
    """
    Creates an as-built joint between two component occurrences (at their current positions).
    joint_type: "rigid" or "revolute".
    """
    return await send_to_addin('create_as_built_joint', {
        "component1_name": component1_name,
        "component2_name": component2_name,
        "joint_type": joint_type
    })

@mcp.tool()
async def delete_user_parameter(name: str) -> Dict[str, Any]:
    """
    Deletes an existing user parameter by name.
    """
    return await send_to_addin('delete_user_parameter', {"name": name})

@mcp.tool()
async def capture_screenshot(
    file_path: str,
    width: int = 1280,
    height: int = 720,
    send_to_mcp: bool = False,
    local_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Captures a screenshot of the active viewport.
    file_path: The absolute path to save the image ON THE FUSION 360 MACHINE.
    send_to_mcp: If True, the image is sent over the network.
    local_file_path: If send_to_mcp is True, the absolute path to save the image ON THE MCP HOST MACHINE.
    """
    if send_to_mcp and not local_file_path:
        raise Exception("local_file_path must be provided if send_to_mcp is True.")

    response = await send_to_addin('capture_screenshot', {
        "file_path": file_path,
        "width": width,
        "height": height,
        "send_to_mcp": send_to_mcp
    })

    if send_to_mcp and "file_content_base64" in response and isinstance(local_file_path, str):
        import base64
        with open(local_file_path, "wb") as f:
            f.write(base64.b64decode(response["file_content_base64"]))
        response["local_file_path"] = local_file_path

    return response

@mcp.tool()
async def list_projects() -> Dict[str, Any]:
    """
    Lists all available projects in the active Fusion 360 Hub.
    Projects are the top-level containers for all data.
    """
    return await send_to_addin('list_projects', {})

@mcp.tool()
async def create_project(name: str) -> Dict[str, Any]:
    """
    Creates a new project in the active hub.
    """
    return await send_to_addin('create_project', {"name": name})

@mcp.tool()
async def create_folder(
    project_name: str,
    folder_name: str,
    parent_folder_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new folder within a project's root or a subfolder.
    
    Arguments:
    - parent_folder_path: Optional, e.g., "Designs/2024" (uses '/' as delimiter).
    """
    return await send_to_addin('create_folder', {
        "project_name": project_name,
        "folder_name": folder_name,
        "parent_folder_path": parent_folder_path
    })

@mcp.tool()
async def create_new_design(
    name: str,
    project_name: Optional[str] = None,
    folder_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates and saves a new Fusion 360 design file.
    
    Arguments:
    - project_name, folder_path: Optional location to save the design.
    """
    return await send_to_addin('create_new_design', {
        "name": name,
        "project_name": project_name,
        "folder_path": folder_path
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fusion 360 MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"], 
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport type (default: stdio)"
    )
    parser.add_argument(
        "--host", 
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="Host for SSE transport (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.environ.get("MCP_PORT", 8000)),
        help="Port for SSE transport (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.transport == "sse":
        import uvicorn
        print(f"Starting SSE server on {args.host}:{args.port}")
        uvicorn.run(mcp.sse_app, host=args.host, port=args.port)
    else:
        mcp.run(transport='stdio')
