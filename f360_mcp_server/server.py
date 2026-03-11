import asyncio
import json
import socket
import sys
import uuid
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# Configuration
ADDIN_HOST = '127.0.0.1'
ADDIN_PORT = 30011

mcp = FastMCP("fusion360-mcp")

async def send_to_addin(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to send JSON-RPC to the Fusion 360 Add-In."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(uuid.uuid4())
    }
    
    # We use a blocking socket here but wrap it in an asyncio executor
    # or just use asyncio sockets. For simplicity, we'll try standard sockets
    # since these are fast local calls.
    
    def sync_request():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0) # 5 second timeout
            s.connect((ADDIN_HOST, ADDIN_PORT))
            s.sendall(json.dumps(request).encode('utf-8') + b'\n')
            
            # Read response
            buffer = ""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                if '\n' in buffer:
                    break
            
            return buffer.strip()

    try:
        response_data = await asyncio.to_thread(sync_request)
        response = json.loads(response_data)
        
        if "error" in response:
            raise Exception(f"Fusion 360 Error: {response['error']}")
            
        return response.get("result", {})
    except ConnectionRefusedError:
        raise Exception(f"Could not connect to Fusion 360 Add-In at {ADDIN_HOST}:{ADDIN_PORT}. Is it running?")
    except json.JSONDecodeError:
        raise Exception("Invalid response from Fusion 360 Add-In.")

@mcp.tool()
async def create_sketch(plane_name: str = "XY") -> Dict[str, Any]:
    """
    Creates a new empty sketch in the active Fusion 360 design.
    Plane name can be "XY", "XZ", or "YZ".
    Returns the newly created sketch name.
    """
    return await send_to_addin('create_sketch', {"plane_name": plane_name})

@mcp.tool()
async def add_circle(sketch_name: str, x: float, y: float, radius: float) -> Dict[str, Any]:
    """
    Adds a circle to an existing sketch in Fusion 360.
    Dimensions are in centimeters (cm).
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
    Adds a line to an existing sketch in Fusion 360.
    Dimensions are in centimeters (cm).
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
    Adds a rectangle to an existing sketch in Fusion 360.
    rect_type: "two_point" (default), "three_point", or "center".
    For "two_point": (x1,y1) and (x2,y2) are opposite corners.
    For "three_point": (x1,y1), (x2,y2), (x3,y3) define three corners.
    For "center": (x1,y1) is center, (x2,y2) is a corner.
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
    For "three_point": (x1,y1)=start, (x2,y2)=point_on_arc, (x3,y3)=end.
    For "center_start_sweep": (x1,y1)=center, (x2,y2)=start, x3=sweep_angle (in radians).
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
    Adds a fitted spline through a list of points.
    points: A list of [x, y] coordinate pairs, e.g., [[0,0], [1,1], [2,0]].
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
    Adds a regular polygon.
    poly_type: "inscribed" or "circumscribed".
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
    Adds an ellipse.
    (center_x, center_y) is the center point.
    (major_x, major_y) defines the major axis radius and orientation.
    (minor_x, minor_y) defines a point on the minor axis.
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
    Applies a geometric constraint between one or two sketch entities.
    constraint_type: "coincident", "collinear", "concentric", "midpoint", "parallel", "perpendicular", "horizontal", "vertical", "tangent", "equal".
    entity types can be: "line", "line_start", "line_end", "circle", "circle_center", "arc", "arc_start", "arc_end", "arc_center", "point".
    entity index is the 0-based index of that geometry type created in the sketch.
    For horizontal/vertical on a single line, omit ent2.
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
    Adds a distance dimension between two sketch entities.
    orientation: "aligned", "horizontal", or "vertical"
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
    """Adds a radial dimension to an arc or circle."""
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
    """Adds a diameter dimension to a circle or arc."""
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
    Creates an offset of a sketch entity by a specified distance.
    Distance is in cm. Positive or negative determines direction.
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
    Extrudes a specific closed profile from a sketch to a specific distance in cm.
    operation can be 'new_body', 'join', 'cut', or 'intersect'.
    profile_index is 0-indexed. 0 is usually the outer profile.
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
    Revolves a specific closed profile around an axis entity to a specific angle in degrees.
    operation can be 'new_body', 'join', 'cut', or 'intersect'.
    axis_ent_type typically "line" from the same sketch.
    profile_index is 0-indexed. 0 is usually the outer profile.
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
    Combines multiple tool bodies into a target body.
    operation can be 'join', 'cut', or 'intersect'.
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
    Creates a simple hole from a specific point in a sketch.
    Diameter and depth are in cm.
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
    Hollows out a specified body to a specific thickness in cm.
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
    Fillets all edges of a specified body to a specific radius in cm.
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
    Chamfers all edges of a specified body to a specific distance in cm.
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
    Creates a loft feature from multiple sketch profiles.
    profiles_info should be a list of objects like: [{"sketch_name": "sk1", "profile_idx": 0}, {"sketch_name": "sk2", "profile_idx": 0}]
    """
    return await send_to_addin('create_loft', {
        "profiles_info": profiles_info
    })

if __name__ == "__main__":
    mcp.run(transport='stdio')
