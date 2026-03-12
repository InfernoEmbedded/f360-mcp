import adsk.core
import adsk.fusion
import math
from . import command
from .base import get_active_design

@command()
def create_offset_plane(app, base_plane, offset):
    design = get_active_design(app)
    rootComp = design.rootComponent
    planes = rootComp.constructionPlanes
    if base_plane.upper() == "XY":
        base = rootComp.xYConstructionPlane
    elif base_plane.upper() == "XZ":
        base = rootComp.xZConstructionPlane
    elif base_plane.upper() == "YZ":
        base = rootComp.yZConstructionPlane
    else:
        base = planes.itemByName(base_plane)
        if not base:
            raise Exception(f"Base plane '{base_plane}' not found.")
    planeInput = planes.createInput()
    offsetValue = adsk.core.ValueInput.createByReal(offset)
    planeInput.setByOffset(base, offsetValue)
    plane = planes.add(planeInput)
    return {"message": f"Offset plane created from {base_plane} by {offset}cm.", "plane_name": plane.name}

@command()
def create_plane_at_angle(app, axis_name, angle_deg):
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
    return {"message": f"Angled plane created around {axis_name} at {angle_deg} degrees.", "plane_name": plane.name}

@command()
def list_construction(app):
    design = get_active_design(app)
    rootComp = design.rootComponent
    planes = [{"name": p.name, "type": "plane", "is_visible": p.isVisible} for p in rootComp.constructionPlanes]
    axes = [{"name": a.name, "type": "axis", "is_visible": a.isVisible} for a in rootComp.constructionAxes]
    points = [{"name": pt.name, "type": "point", "is_visible": pt.isVisible} for pt in rootComp.constructionPoints]
    return {"planes": planes, "axes": axes, "points": points}

@command()
def rename_construction(app, old_name, new_name, type="plane"):
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
