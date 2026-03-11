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

def add_rectangle(app, sketch_name, x1, y1, x2, y2, x3=None, y3=None, rect_type="two_point"):
    """
    Adds a rectangle to an existing sketch.
    rect_type can be "two_point", "three_point", or "center".
    """
    sketch = get_sketch_by_name(app, sketch_name)
    lines = sketch.sketchCurves.sketchLines
    
    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    
    if rect_type == "three_point" and x3 is not None and y3 is not None:
        p3 = adsk.core.Point3D.create(x3, y3, 0)
        lines.addThreePointRectangle(p1, p2, p3)
        return {"message": "Three-point rectangle added."}
    elif rect_type == "center":
        lines.addCenterPointRectangle(p1, p2) # p1=center, p2=corner
        return {"message": "Center-point rectangle added."}
    else:
        lines.addTwoPointRectangle(p1, p2)
        return {"message": "Two-point rectangle added."}

def add_arc(app, sketch_name, x1, y1, x2, y2, x3, y3, arc_type="three_point"):
    """
    Adds an arc.
    three_point: x1,y1=start, x2,y2=point_on, x3,y3=end
    center_start_sweep: x1,y1=center, x2,y2=start, x3=sweep_angle (radians)
    """
    sketch = get_sketch_by_name(app, sketch_name)
    arcs = sketch.sketchCurves.sketchArcs
    
    if arc_type == "center_start_sweep":
        center = adsk.core.Point3D.create(x1, y1, 0)
        start = adsk.core.Point3D.create(x2, y2, 0)
        sweep = x3 # Overloading x3 as angle
        arcs.addByCenterStartSweep(center, start, sweep)
        return {"message": "Center-start-sweep arc added."}
    else:
        p1 = adsk.core.Point3D.create(x1, y1, 0)
        p2 = adsk.core.Point3D.create(x2, y2, 0)
        p3 = adsk.core.Point3D.create(x3, y3, 0)
        arcs.addByThreePoints(p1, p2, p3)
        return {"message": "Three-point arc added."}

def add_spline(app, sketch_name, points):
    """
    Adds a fitted spline through a list of (x, y) coordinates.
    points: list of [x, y] lists.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    splines = sketch.sketchCurves.sketchFittedSplines
    
    points_collection = adsk.core.ObjectCollection.create()
    for pt in points:
        points_collection.add(adsk.core.Point3D.create(pt[0], pt[1], 0))
        
    splines.add(points_collection)
    return {"message": f"Spline added with {len(points)} points."}

def add_polygon(app, sketch_name, center_x, center_y, num_sides, vertex_x, vertex_y, poly_type="inscribed"):
    """
    Adds a regular polygon.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    polygons = sketch.sketchPolygons
    
    center = adsk.core.Point3D.create(center_x, center_y, 0)
    vertex = adsk.core.Point3D.create(vertex_x, vertex_y, 0)
    
    if poly_type == "circumscribed":
        polygons.addCircumscribedPolygon(center, num_sides, vertex)
    else:
        polygons.addInscribedPolygon(center, num_sides, vertex)
        
    return {"message": f"{poly_type.capitalize()} polygon with {num_sides} sides added."}

def add_ellipse(app, sketch_name, center_x, center_y, major_x, major_y, minor_x, minor_y):
    """
    Adds an ellipse.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    ellipses = sketch.sketchCurves.sketchEllipses
    
    center = adsk.core.Point3D.create(center_x, center_y, 0)
    major = adsk.core.Point3D.create(major_x, major_y, 0)
    minor = adsk.core.Point3D.create(minor_x, minor_y, 0)
    
    ellipses.add(center, major, minor)
    return {"message": "Ellipse added."}

def add_point(app, sketch_name, x, y):
    """
    Adds a sketch point.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    points = sketch.sketchPoints
    
    p = adsk.core.Point3D.create(x, y, 0)
    points.add(p)
    return {"message": f"Point added at ({x}, {y})."}

def add_text(app, sketch_name, text, x, y, height=0.5):
    """
    Adds text to a sketch.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    texts = sketch.sketchTexts
    
    position = adsk.core.Point3D.create(x, y, 0)
    input = texts.createInput(text, height, position)
    texts.add(input)
    return {"message": f"Text '{text}' added at ({x}, {y})."}

# --- Constraint Helpers and Commands ---

def resolve_entity(sketch, entity_type, index):
    """
    Resolves a string entity_type and integer index to a physical Fusion 360 SketchEntity.
    Examples format: "line", "line_start", "line_end", "circle", "circle_center", "arc_start", "point", etc.
    """
    parts = entity_type.split('_')
    base_type = parts[0]
    sub_type = parts[1] if len(parts) > 1 else None
    
    ent = None
    if base_type == "line":
        ent = sketch.sketchCurves.sketchLines.item(index)
        if sub_type == "start": return ent.startSketchPoint
        if sub_type == "end": return ent.endSketchPoint
    elif base_type == "circle":
        ent = sketch.sketchCurves.sketchCircles.item(index)
        if sub_type == "center": return ent.centerSketchPoint
    elif base_type == "arc":
        ent = sketch.sketchCurves.sketchArcs.item(index)
        if sub_type == "center": return ent.centerSketchPoint
        if sub_type == "start": return ent.startSketchPoint
        if sub_type == "end": return ent.endSketchPoint
    elif base_type == "spline":
        ent = sketch.sketchCurves.sketchFittedSplines.item(index)
    elif base_type == "ellipse":
        ent = sketch.sketchCurves.sketchEllipses.item(index)
        if sub_type == "center": return ent.centerSketchPoint
    elif base_type == "point":
        return sketch.sketchPoints.item(index)
        
    if ent:
        return ent
    raise Exception(f"Unable to resolve entity: {entity_type} at index {index}")

def apply_constraint(app, sketch_name, constraint_type, ent1_type, ent1_idx, ent2_type=None, ent2_idx=None):
    """
    Applies a geometric constraint between one or two sketch entities.
    constraint_type can be: "coincident", "collinear", "concentric", "midpoint", "parallel", "perpendicular", "horizontal", "vertical", "tangent", "equal", "symmetry"
    (Note: symmetry requires ent3 which we will handle separately or overload ent2. Actually, let's keep symmetry out of this generic function for now or adapt).
    """
    sketch = get_sketch_by_name(app, sketch_name)
    constraints = sketch.geometricConstraints
    
    e1 = resolve_entity(sketch, ent1_type, ent1_idx)
    e2 = resolve_entity(sketch, ent2_type, ent2_idx) if ent2_type else None
    
    try:
        if constraint_type == "coincident":
            c = constraints.addCoincident(e1, e2)
        elif constraint_type == "collinear":
            c = constraints.addCollinear(e1, e2)
        elif constraint_type == "concentric":
            c = constraints.addConcentric(e1, e2)
        elif constraint_type == "midpoint":
            c = constraints.addMidPoint(e1, e2) # e1=point, e2=curve
        elif constraint_type == "parallel":
            c = constraints.addParallel(e1, e2)
        elif constraint_type == "perpendicular":
            c = constraints.addPerpendicular(e1, e2)
        elif constraint_type == "horizontal":
            if e2: constraints.addHorizontalPoints(e1, e2)
            else: constraints.addHorizontal(e1) # e1=line
        elif constraint_type == "vertical":
            if e2: constraints.addVerticalPoints(e1, e2)
            else: constraints.addVertical(e1) # e1=line
        elif constraint_type == "tangent":
            c = constraints.addTangent(e1, e2)
        elif constraint_type == "equal":
            c = constraints.addEqual(e1, e2)
        else:
            raise Exception(f"Unknown constraint type: {constraint_type}")
            
        return {"message": f"Successfully added {constraint_type} constraint."}
    except Exception as e:
        raise Exception(f"Failed to add {constraint_type} constraint: {str(e)}")

def add_symmetry_constraint(app, sketch_name, ent1_type, ent1_idx, ent2_type, ent2_idx, sym_line_type, sym_line_idx):
    sketch = get_sketch_by_name(app, sketch_name)
    constraints = sketch.geometricConstraints
    
    e1 = resolve_entity(sketch, ent1_type, ent1_idx)
    e2 = resolve_entity(sketch, ent2_type, ent2_idx)
    sym_line = resolve_entity(sketch, sym_line_type, sym_line_idx)
    
    constraints.addSymmetry(e1, e2, sym_line)
    return {"message": "Successfully added symmetry constraint."}

# --- Dimension Commands ---

def add_distance_dimension(app, sketch_name, ent1_type, ent1_idx, ent2_type, ent2_idx, text_x, text_y, orientation="aligned"):
    """
    orientation: "aligned", "horizontal", or "vertical"
    """
    sketch = get_sketch_by_name(app, sketch_name)
    dims = sketch.sketchDimensions
    
    e1 = resolve_entity(sketch, ent1_type, ent1_idx)
    e2 = resolve_entity(sketch, ent2_type, ent2_idx)
    text_pos = adsk.core.Point3D.create(text_x, text_y, 0)
    
    orient_enum = adsk.fusion.DimensionOrientations.AlignedDimensionOrientation
    if orientation == "horizontal":
        orient_enum = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    elif orientation == "vertical":
        orient_enum = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
        
    dim = dims.addDistanceDimension(e1, e2, orient_enum, text_pos)
    return {"message": "Distance dimension added.", "value": dim.parameter.value}

def add_radial_dimension(app, sketch_name, ent_type, ent_idx, text_x, text_y):
    sketch = get_sketch_by_name(app, sketch_name)
    dims = sketch.sketchDimensions
    
    e1 = resolve_entity(sketch, ent_type, ent_idx)
    text_pos = adsk.core.Point3D.create(text_x, text_y, 0)
    
    dim = dims.addRadialDimension(e1, text_pos)
    return {"message": "Radial dimension added.", "value": dim.parameter.value}

def add_diameter_dimension(app, sketch_name, ent_type, ent_idx, text_x, text_y):
    sketch = get_sketch_by_name(app, sketch_name)
    dims = sketch.sketchDimensions
    
    e1 = resolve_entity(sketch, ent_type, ent_idx)
    text_pos = adsk.core.Point3D.create(text_x, text_y, 0)
    
    dim = dims.addDiameterDimension(e1, text_pos)
    return {"message": "Diameter dimension added.", "value": dim.parameter.value}

def add_angular_dimension(app, sketch_name, line1_idx, line2_idx, text_x, text_y):
    sketch = get_sketch_by_name(app, sketch_name)
    dims = sketch.sketchDimensions
    
    line1 = resolve_entity(sketch, "line", line1_idx)
    line2 = resolve_entity(sketch, "line", line2_idx)
    text_pos = adsk.core.Point3D.create(text_x, text_y, 0)
    
    dim = dims.addAngularDimension(line1, line2, text_pos)
    return {"message": "Angular dimension added.", "value": dim.parameter.value}
