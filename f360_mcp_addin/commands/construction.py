import adsk.core
import adsk.fusion
import math
from . import command
from .base import get_active_design

@command()
def create_offset_plane(app, name, base_plane, offset):
    """
    Creates a construction plane offset from an existing plane or face.
    
    Offset planes are essential for sketching in 3D space.

    Args:
        name (str): Name for the new plane.
        base_plane (str): "XY", "XZ", "YZ", or a named construction plane/face.
        offset (float): Offset distance in centimeters (cm).

    Examples:
        # Create a plane 10cm above the XY floor
        call_addin("create_offset_plane", {"name": "TopPlane", "base_plane": "XY", "offset": 10.0})
    """

@command()
def create_plane_at_angle(app, name, axis_name, angle_deg):
    """
    Creates a construction plane at an angle relative to an axis.

    Args:
        name (str): Name for the new plane.
        axis_name (str): The axis to rotate around ('X', 'Y', 'Z' or named axis).
        angle_deg (float): Rotation angle in degrees.

    Examples:
        # Create a 45-degree slanted plane around the X axis
        call_addin("create_plane_at_angle", {"name": "SlantPlane", "axis_name": "X", "angle_deg": 45})
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    planes = rootComp.constructionPlanes
    if axis_name.upper() == "X":
        axis = rootComp.xConstructionAxis
        ref_plane = rootComp.xYConstructionPlane
    elif axis_name.upper() == "Y":
        axis = rootComp.yConstructionAxis
        ref_plane = rootComp.xYConstructionPlane
    elif axis_name.upper() == "Z":
        axis = rootComp.zConstructionAxis
        ref_plane = rootComp.xZConstructionPlane
    else:
        axes = rootComp.constructionAxes
        axis = axes.itemByName(axis_name)
        if not axis:
            raise Exception(f"Axis '{axis_name}' not found.")
        ref_plane = None
    planeInput = planes.createInput()
    angleValue = adsk.core.ValueInput.createByReal(math.radians(angle_deg))
    if ref_plane:
        try:
            planeInput.setByAngle(axis, angleValue, ref_plane)
        except:
            planeInput.setByAngle(axis, angleValue)
    else:
        planeInput.setByAngle(axis, angleValue)
    plane = planes.add(planeInput)
    plane.name = name
    return {"message": f"Angled plane '{name}' created around {axis_name} at {angle_deg} degrees.", "plane_name": plane.name}

@command()
def list_construction(app):
    """
    Lists all construction planes, axes, and points in the design.

    Returns:
        dict: {"planes": [...], "axes": [...], "points": [...]}

    Examples:
        call_addin("list_construction", {})
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    planes = [{"name": p.name, "type": "plane", "is_visible": p.isVisible} for p in rootComp.constructionPlanes]
    axes = [{"name": a.name, "type": "axis", "is_visible": a.isVisible} for a in rootComp.constructionAxes]
    points = [{"name": pt.name, "type": "point", "is_visible": pt.isVisible} for pt in rootComp.constructionPoints]
    return {"planes": planes, "axes": axes, "points": points}

@command()
def rename_construction(app, old_name, new_name, type="plane"):
    """
    Renames a construction entity.

    Args:
        old_name (str): Current name.
        new_name (str): New name.
        type (str): 'plane', 'axis', or 'point'. Default: 'plane'.

    Examples:
        call_addin("rename_construction", {"old_name": "Plane1", "new_name": "MirrorPlane"})
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    item = None
    if type == "plane":
        item = rootComp.constructionPlanes.itemByName(old_name)
    elif type == "axis":
        item = rootComp.constructionAxes.itemByName(old_name)
    elif type == "point":
        item = rootComp.constructionPoints.itemByName(old_name)
    if not item:
        raise Exception(f"Construction {type} '{old_name}' not found.")
    item.name = new_name
    return {"message": f"Renamed {type} '{old_name}' to '{new_name}'"}

@command()
def delete_construction(app, name, type="plane"):
    """
    Deletes a construction entity.

    Args:
        name (str): Name of the entity to delete.
        type (str): 'plane', 'axis', or 'point'. Default: 'plane'.

    Examples:
        call_addin("delete_construction", {"name": "Plane1"})
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    item = None
    if type == "plane":
        item = rootComp.constructionPlanes.itemByName(name)
    elif type == "axis":
        item = rootComp.constructionAxes.itemByName(name)
    elif type == "point":
        item = rootComp.constructionPoints.itemByName(name)
    if not item:
        raise Exception(f"Construction {type} '{name}' not found.")
    item.deleteMe()
    return {"message": f"Deleted {type} '{name}'"}
