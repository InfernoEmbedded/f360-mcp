import adsk.core
import adsk.fusion

def get_active_design(app):
    design = app.activeProduct
    if not design or type(design) is not adsk.fusion.Design:
        raise Exception("No active Fusion 360 design.")
    return design

def create_sketch(app, plane_name="XY"):
    """
    Creates a new sketch on the specified base plane.
    plane_name can be "XY", "XZ", or "YZ".
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    planes = rootComp.xYConstructionPlane
    if plane_name.upper() == "XZ":
        planes = rootComp.xZConstructionPlane
    elif plane_name.upper() == "YZ":
        planes = rootComp.yZConstructionPlane
        
    sketches = rootComp.sketches
    sketch = sketches.add(planes)
    sketch.name = f"MCP_Sketch_{plane_name}"
    
    # Return the index of the sketch so it can be referenced later
    sketch_index = sketch.creationIndex # We can return index or name
    return {"sketch_name": sketch.name, "message": "Sketch created successfully"}

def get_sketch_by_name(app, sketch_name):
    design = get_active_design(app)
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sketch = sketches.itemByName(sketch_name)
    if not sketch:
        raise Exception(f"Sketch named {sketch_name} not found.")
    return sketch

def add_circle(app, sketch_name, x, y, radius):
    """
    Adds a circle to an existing sketch.
    Parameters are in cm (Fusion 360 default internal unit).
    """
    sketch = get_sketch_by_name(app, sketch_name)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(x, y, 0)
    circle = circles.addByCenterRadius(center, radius)
    return {"message": f"Circle added at ({x},{y}) with radius {radius}"}

def add_line(app, sketch_name, x1, y1, x2, y2):
    """
    Adds a line to an existing sketch.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    lines = sketch.sketchCurves.sketchLines
    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    line = lines.addByTwoPoints(p1, p2)
    return {"message": f"Line added from ({x1},{y1}) to ({x2},{y2})"}
