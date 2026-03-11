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

# --- Utilities & Operations ---

def list_sketches(app):
    design = get_active_design(app)
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    
    sketch_list = []
    for i in range(sketches.count):
        sketch = sketches.item(i)
        sketch_list.append({"name": sketch.name, "index": i})
        
    return {"sketches": sketch_list}

def delete_sketch(app, sketch_name):
    sketch = get_sketch_by_name(app, sketch_name)
    sketch.deleteMe()
    return {"message": f"Sketch '{sketch_name}' deleted."}

def project_geometry(app, sketch_name, ent_type, ent_idx, from_sketch_name=None):
    """
    Projects geometry from another sketch into the active sketch.
    If from_sketch_name is None, it tries to project from the same sketch (which may not make sense, 
    but we allow resolving it from either the active sketch or another sketch).
    Usually you project body edges or origin planes, but for this API we stick to sketch entities.
    """
    target_sketch = get_sketch_by_name(app, sketch_name)
    source_sketch = get_sketch_by_name(app, from_sketch_name) if from_sketch_name else target_sketch
    
    ent = resolve_entity(source_sketch, ent_type, ent_idx)
    projected_curves = target_sketch.project(ent)
    
    return {"message": f"Projected {len(projected_curves)} curves."}

def offset_geometry(app, sketch_name, ent_type, ent_idx, offset_distance):
    """
    Creates an offset of a sketch entity.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    ent = resolve_entity(sketch, ent_type, ent_idx)
    
    # In Fusion 360 API, offset requires an ObjectCollection of connected curves
    curves = adsk.core.ObjectCollection.create()
    curves.add(ent)
    
    dir_point = adsk.core.Point3D.create(0, 0, 0) # Just a reference point for direction
    
    # offset() is an older method, but it exists on Sketch
    offset_curves = sketch.offset(curves, dir_point, offset_distance)
    return {"message": f"Created offset with {len(offset_curves)} curves."}

def delete_sketch_entity(app, sketch_name, ent_type, ent_idx):
    """
    Deletes a specific entity from a sketch.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    ent = resolve_entity(sketch, ent_type, ent_idx)
    ent.deleteMe()
    return {"message": f"Entity '{ent_type}' at index {ent_idx} deleted."}

def trim_sketch_geometry(app, sketch_name, ent_type, ent_idx, x, y):
    """
    Trims a sketch curve around the provided (x, y) coordinates.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    ent = resolve_entity(sketch, ent_type, ent_idx)
    
    # Needs a 3D point indicating where to trim the curve
    pt = adsk.core.Point3D.create(x, y, 0)
    
    if hasattr(ent, 'trim'):
        new_curves = ent.trim(pt)
        count = new_curves.count if new_curves else 0
        return {"message": f"Trimmed curve resulting in {count} new pieces."}
    else:
        raise Exception(f"Entity type {ent_type} does not support trimming.")

# --- Solid Modeling (Features) ---

def create_extrude(app, sketch_name, distance, operation="new_body", profile_index=0):
    """
    Extrudes a profile from a sketch to a specific distance.
    operation can be 'new_body', 'join', 'cut', or 'intersect'.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    extrudes = rootComp.features.extrudeFeatures
    
    sketch = get_sketch_by_name(app, sketch_name)
    if sketch.profiles.count == 0:
        raise Exception(f"Sketch '{sketch_name}' does not contain any closed profiles to extrude.")
        
    if profile_index >= sketch.profiles.count:
        raise Exception(f"Profile index {profile_index} is out of bounds for sketch '{sketch_name}'.")
        
    profile = sketch.profiles.item(profile_index)
    
    # Define distance value (in cm)
    distance_val = adsk.core.ValueInput.createByReal(distance)
    
    # Map string to Fusion operation enum
    op_map = {
        "new_body": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation
    }
    fusion_op = op_map.get(operation.lower(), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    
    extrudeInput = extrudes.createInput(profile, fusion_op)
    extrudeInput.setDistanceExtent(False, distance_val)
    
    extrude = extrudes.add(extrudeInput)
    return {"message": f"Extruded {distance}cm using operation {operation}.", "feature_name": extrude.name}

def create_revolve(app, sketch_name, axis_ent_type, axis_ent_idx, angle, operation="new_body", profile_index=0):
    """
    Revolves a profile from a sketch around an axis to a specific angle.
    angle is in degrees.
    """
    import math
    design = get_active_design(app)
    rootComp = design.rootComponent
    revolves = rootComp.features.revolveFeatures
    
    sketch = get_sketch_by_name(app, sketch_name)
    if sketch.profiles.count == 0:
        raise Exception(f"Sketch '{sketch_name}' does not contain any closed profiles to revolve.")
        
    if profile_index >= sketch.profiles.count:
        raise Exception(f"Profile index {profile_index} is out of bounds for sketch '{sketch_name}'.")
        
    profile = sketch.profiles.item(profile_index)
    axis = resolve_entity(sketch, axis_ent_type, axis_ent_idx)
    
    angle_rad = math.radians(angle)
    angle_val = adsk.core.ValueInput.createByReal(angle_rad)
    
    op_map = {
        "new_body": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation
    }
    fusion_op = op_map.get(operation.lower(), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    
    revolveInput = revolves.createInput(profile, axis, fusion_op)
    revolveInput.setAngleExtent(False, angle_val)
    
    revolve = revolves.add(revolveInput)
    return {"message": f"Revolved {angle} degrees using operation {operation}.", "feature_name": revolve.name}

def create_sweep(app, profile_sketch_name, path_sketch_name, path_ent_type, path_ent_idx, operation="new_body", profile_index=0):
    """
    Sweeps a profile along a path entity.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    sweeps = rootComp.features.sweepFeatures
    
    prof_sketch = get_sketch_by_name(app, profile_sketch_name)
    if prof_sketch.profiles.count == 0:
        raise Exception(f"Sketch '{profile_sketch_name}' does not contain any closed profiles to sweep.")
        
    if profile_index >= prof_sketch.profiles.count:
        raise Exception(f"Profile index {profile_index} is out of bounds for sketch '{profile_sketch_name}'.")
        
    profile = prof_sketch.profiles.item(profile_index)
    
    path_sketch = get_sketch_by_name(app, path_sketch_name)
    path_ent = resolve_entity(path_sketch, path_ent_type, path_ent_idx)
    
    # Create the path object needed for sweep
    path = rootComp.features.createPath(path_ent)
    
    op_map = {
        "new_body": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation
    }
    fusion_op = op_map.get(operation.lower(), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    
    sweepInput = sweeps.createInput(profile, path, fusion_op)
    
    sweep = sweeps.add(sweepInput)
    return {"message": f"Sweep created using operation {operation}.", "feature_name": sweep.name}

def list_bodies(app):
    """Lists all bodies in the active design."""
    design = get_active_design(app)
    bodies_list = []
    for i in range(design.rootComponent.bRepBodies.count):
        body = design.rootComponent.bRepBodies.item(i)
        bodies_list.append({"name": body.name, "index": i})
    return {"bodies": bodies_list}

def combine_bodies(app, target_body_name, tool_body_names, operation="join"):
    """
    Combines bodies.
    operation can be 'join', 'cut', or 'intersect'.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    combines = rootComp.features.combineFeatures
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    target = get_body(target_body_name)
    tools = adsk.core.ObjectCollection.create()
    for t_name in tool_body_names:
        tools.add(get_body(t_name))
        
    combineInput = combines.createInput(target, tools)
    
    op_map = {
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation
    }
    combineInput.operation = op_map.get(operation.lower(), adsk.fusion.FeatureOperations.JoinFeatureOperation)
    
    combine = combines.add(combineInput)
    return {"message": f"Combined bodies using {operation}.", "feature_name": combine.name}

def create_hole(app, sketch_name, point_idx, diameter, depth):
    """
    Creates a simple hole on a sketch point.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    holes = rootComp.features.holeFeatures
    
    sketch = get_sketch_by_name(app, sketch_name)
    if point_idx >= sketch.sketchPoints.count:
        raise Exception(f"Point index {point_idx} is out of bounds for sketch '{sketch_name}'.")
        
    point = sketch.sketchPoints.item(point_idx)
    
    diameter_val = adsk.core.ValueInput.createByReal(diameter)
    depth_val = adsk.core.ValueInput.createByReal(depth)
    
    holeInput = holes.createSimpleInput(diameter_val)
    holeInput.setPositionBySketchPoint(point)
    holeInput.setDistanceExtent(depth_val)
    
    hole = holes.add(holeInput)
    return {"message": f"Hole created with diameter {diameter}cm and depth {depth}cm.", "feature_name": hole.name}

def create_shell(app, body_name, thickness):
    """
    Hollows out a body to a specific thickness.
    thickness is in cm.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    shells = rootComp.features.shellFeatures
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    entities = adsk.core.ObjectCollection.create()
    entities.add(body)
    
    thickness_val = adsk.core.ValueInput.createByReal(thickness)
    shellInput = shells.createInput(entities, False)
    shellInput.insideThickness = thickness_val
    
    shell = shells.add(shellInput)
    return {"message": f"Shell created with {thickness}cm thickness.", "feature_name": shell.name}

def create_fillet(app, body_name, radius):
    """
    Fillets all edges of a body to a specific radius in cm.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    fillets = rootComp.features.filletFeatures
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    edges = adsk.core.ObjectCollection.create()
    for i in range(body.edges.count):
        edges.add(body.edges.item(i))
        
    radius_val = adsk.core.ValueInput.createByReal(radius)
    filletInput = fillets.createInput()
    filletInput.addConstantRadiusEdgeSet(edges, radius_val, True)
    
    fillet = fillets.add(filletInput)
    return {"message": f"Filleted all edges of body {body_name} with {radius}cm radius.", "feature_name": fillet.name}

def create_chamfer(app, body_name, distance):
    """
    Chamfers all edges of a body to a specific distance in cm.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    chamfers = rootComp.features.chamferFeatures
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    edges = adsk.core.ObjectCollection.create()
    for i in range(body.edges.count):
        edges.add(body.edges.item(i))
        
    distance_val = adsk.core.ValueInput.createByReal(distance)
    chamferInput = chamfers.createInput(edges, True)
    chamferInput.setToEqualDistance(distance_val)
    
    chamfer = chamfers.add(chamferInput)
    return {"message": f"Chamfered all edges of body {body_name} with {distance}cm distance.", "feature_name": chamfer.name}

def feature_mirror(app, body_name, plane_name):
    """
    Mirrors a body across an origin plane ('xy', 'yz', 'xz').
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    mirrors = rootComp.features.mirrorFeatures
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    
    plane_map = {
        'xy': rootComp.xYConstructionPlane,
        'yz': rootComp.yZConstructionPlane,
        'xz': rootComp.xZConstructionPlane,
        'zx': rootComp.xZConstructionPlane
    }
    plane = plane_map.get(plane_name.lower())
    if not plane:
        raise Exception(f"Invalid plane '{plane_name}'. Use 'xy', 'yz', or 'xz'.")
        
    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)
    
    mirrorInput = mirrors.createInput(inputEntities, plane)
    mirror = mirrors.add(mirrorInput)
    return {"message": f"Mirrored body {body_name} across {plane_name} plane.", "feature_name": mirror.name}

def create_loft(app, profiles_info):
    """
    Creates a loft feature from multiple sketch profiles.
    profiles_info is a list of dicts: [{'sketch_name': 'sk1', 'profile_idx': 0}, ...]
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    lofts = rootComp.features.loftFeatures
    
    loftInput = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    loftSections = loftInput.loftSections
    
    for p_info in profiles_info:
        sketch = get_sketch_by_name(app, p_info['sketch_name'])
        idx = p_info.get('profile_idx', 0)
        if idx >= sketch.profiles.count:
            raise Exception(f"Profile {idx} not found in sketch '{p_info['sketch_name']}'")
        
        prof = sketch.profiles.item(idx)
        loftSections.add(prof)
        
    loftInput.isSolid = True
    loft = lofts.add(loftInput)
    return {"message": f"Created loft from {len(profiles_info)} profiles.", "feature_name": loft.name}

def execute_script(app, script_code):
    """
    Executes an arbitrary block of Python code in the Fusion 360 context.
    The script has access to 'app' (adsk.core.Application.get()) and 'ui'.
    It must define a variable 'result' if you want it returned.
    """
    import adsk.core
    import traceback
    
    ui = app.userInterface
    
    # Create the global namespace for the script execution
    exec_globals = {
        'app': app,
        'ui': ui,
        'adsk': adsk,
        'result': None
    }
    
    try:
        # We execute the script in the context of the defined globals.
        # This will securely (relatively) evaluate the arbitrary python code provided. 
        # CAUTION: Exec is inherently dangerous if the source of the code is untrusted. 
        # Since this is an LLM writing scripts for a local user, it's an acceptable risk here.
        exec(script_code, exec_globals)
        
        # We attempt to retrieve whatever 'result' the script generated.
        return {"message": "Script executed successfully.", "result": exec_globals.get('result')}
    except Exception as e:
        error_info = traceback.format_exc()
        raise Exception(f"Script Error: {str(e)}\n\nTraceback:\n{error_info}")


