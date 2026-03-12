import adsk.core
import adsk.fusion

_group_stack = []

def get_active_design(app):
    design = app.activeProduct
    if not design or type(design) is not adsk.fusion.Design:
        raise Exception("No active Fusion 360 design.")
    return design

def create_sketch(app, plane_name="XY", body_name=None, face_index=None):
    """
    Creates a new sketch.
    To sketch on an origin plane or construction plane, use `plane_name` ("XY", "XZ", "YZ", or name).
    To sketch on a solid face, provide `body_name` and `face_index` (from find_faces tool).
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    if body_name is not None and face_index is not None:
        def get_body(name):
            for i in range(rootComp.bRepBodies.count):
                b = rootComp.bRepBodies.item(i)
                if b.name == name:
                    return b
            raise Exception(f"Body '{name}' not found.")
        body = get_body(body_name)
        if face_index < 0 or face_index >= body.faces.count:
            raise Exception(f"Face index {face_index} out of bounds.")
        planes = body.faces.item(face_index)
        name_suffix = f"Face{face_index}"
    else:
        if plane_name.upper() == "XY":
            planes = rootComp.xYConstructionPlane
        elif plane_name.upper() == "XZ":
            planes = rootComp.xZConstructionPlane
        elif plane_name.upper() == "YZ":
            planes = rootComp.yZConstructionPlane
        else:
            planes = rootComp.constructionPlanes.itemByName(plane_name)
            if not planes:
                raise Exception(f"Plane '{plane_name}' not found.")
        name_suffix = plane_name
        
    sketches = rootComp.sketches
    sketch = sketches.add(planes)
    sketch.name = f"MCP_Sketch_{name_suffix}"
    
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

def create_offset_plane(app, base_plane, offset):
    """
    Creates a new construction plane offset from a base plane.
    offset is in cm.
    """
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

def create_plane_at_angle(app, axis_name, angle_deg):
    """
    Creates a new construction plane at an angle around an axis.
    axis_name can be "X", "Y", "Z".
    angle_deg is the angle in degrees.
    """
    import math
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
        ref_plane = None # We'd need a reference plane
        
    planeInput = planes.createInput()
    angleValue = adsk.core.ValueInput.createByReal(math.radians(angle_deg))
    if ref_plane:
        try:
            # setByAngle might require planar entity
            planeInput.setByAngle(axis, angleValue, ref_plane)
        except:
            planeInput.setByAngle(axis, angleValue)
    else:
        planeInput.setByAngle(axis, angleValue)
        
    plane = planes.add(planeInput)
    return {"message": f"Angled plane created around {axis_name} at {angle_deg} degrees.", "plane_name": plane.name}

def get_body_properties(app, body_name):
    """
    Returns physical properties of a body: volume, mass, area, bounding box, center of mass.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    phys = body.physicalProperties
    bbox = body.boundingBox
    
    return {
        "body_name": body_name,
        "volume_cm3": round(phys.volume, 3),
        "mass_kg": round(phys.mass, 3),
        "area_cm2": round(phys.area, 3),
        "center_of_mass_cm": {"x": round(phys.centerOfMass.x, 3), "y": round(phys.centerOfMass.y, 3), "z": round(phys.centerOfMass.z, 3)},
        "bounding_box_cm": {
            "min": {"x": round(bbox.minPoint.x, 3), "y": round(bbox.minPoint.y, 3), "z": round(bbox.minPoint.z, 3)},
            "max": {"x": round(bbox.maxPoint.x, 3), "y": round(bbox.maxPoint.y, 3), "z": round(bbox.maxPoint.z, 3)}
        }
    }

def find_faces(app, body_name):
    """
    Returns a list of faces on a body with their index, normals, and area to help identify them.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    faces_info = []
    
    for i in range(body.faces.count):
        face = body.faces.item(i)
        
        geom = face.geometry
        geom_type = geom.objectType.split('::')[-1]
        info = {
            "face_index": i,
            "area_cm2": round(face.area, 3),
            "geometry_type": geom_type,
            "is_planar": (geom_type == "Plane")
        }
        
        pt = face.pointOnFace
        if pt:
            info["center_point"] = {"x": round(pt.x, 3), "y": round(pt.y, 3), "z": round(pt.z, 3)}
            success, normal = face.evaluator.getNormalAtPoint(pt)
            if success:
                normal.normalize()
                info["normal"] = {"x": round(normal.x, 3), "y": round(normal.y, 3), "z": round(normal.z, 3)}
                
        faces_info.append(info)
        
    return {"body_name": body_name, "faces": faces_info}

def create_user_parameter(app, name, expression, unit=""):
    """
    Creates a new user parameter.
    """
    design = get_active_design(app)
    userParams = design.userParameters
    param = userParams.add(name, adsk.core.ValueInput.createByString(expression), unit, "")
    return {"message": f"Created parameter '{name}' = {expression}", "name": param.name, "value": round(param.value, 3)}

def list_user_parameters(app):
    """
    Lists all user parameters.
    """
    design = get_active_design(app)
    userParams = design.userParameters
    params_list = []
    for i in range(userParams.count):
        p = userParams.item(i)
        params_list.append({
            "name": p.name,
            "expression": p.expression,
            "value": round(p.value, 3),
            "unit": p.unit
        })
    return {"parameters": params_list}

def update_user_parameter(app, name, expression):
    """
    Updates an existing user parameter.
    """
    design = get_active_design(app)
    userParams = design.userParameters
    param = userParams.itemByName(name)
    if not param:
        raise Exception(f"Parameter '{name}' not found.")
    param.expression = expression
    return {"message": f"Updated parameter '{name}' to {expression}", "name": param.name, "value": round(param.value, 3)}

def create_component(app, name):
    """
    Creates a new empty component.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    occurrences = rootComp.occurrences
    transform = adsk.core.Matrix3D.create()
    occ = occurrences.addNewComponent(transform)
    comp = occ.component
    comp.name = name
    return {"message": f"Created component '{name}'. Note: modeling still default happens in root component via MCP.", "component_name": comp.name}

def create_rectangular_pattern(app, body_name, count_x, count_y, distance_x, distance_y):
    """
    Creates a rectangular pattern of a body.
    Distances in cm.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)
    
    xAxis = rootComp.xConstructionAxis
    yAxis = rootComp.yConstructionAxis
    
    rectPatterns = rootComp.features.rectangularPatternFeatures
    rectPatternInput = rectPatterns.createInput(inputEntities, xAxis, adsk.core.ValueInput.createByReal(count_x), adsk.core.ValueInput.createByReal(distance_x), adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    
    rectPatternInput.setDirectionTwo(yAxis, adsk.core.ValueInput.createByReal(count_y), adsk.core.ValueInput.createByReal(distance_y))
    
    pattern = rectPatterns.add(rectPatternInput)
    return {"message": f"Created rectangular pattern for '{body_name}'", "pattern_name": pattern.name}

def create_circular_pattern(app, body_name, axis_name, count, angle_deg):
    """
    Creates a circular pattern of a body around an axis.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)
    
    if axis_name.upper() == "X":
        axis = rootComp.xConstructionAxis
    elif axis_name.upper() == "Y":
        axis = rootComp.yConstructionAxis
    elif axis_name.upper() == "Z":
        axis = rootComp.zConstructionAxis
    else:
        axes = rootComp.constructionAxes
        axis = axes.itemByName(axis_name)
        if not axis:
            raise Exception(f"Axis '{axis_name}' not found.")
            
    circPatterns = rootComp.features.circularPatternFeatures
    circPatternInput = circPatterns.createInput(inputEntities, axis)
    circPatternInput.quantity = adsk.core.ValueInput.createByReal(count)
    import math
    circPatternInput.angle = adsk.core.ValueInput.createByReal(math.radians(angle_deg))
    circPatternInput.isSymmetric = False
    
    pattern = circPatterns.add(circPatternInput)
    return {"message": f"Created circular pattern for '{body_name}' around {axis_name}", "pattern_name": pattern.name}

def export_model(app, file_path, file_type="step", body_name=None, send_to_mcp=False):
    """
    Exports the current design or a specific body. file_type can be "step", "stl", or "3mf".
    If send_to_mcp is True, reads the file from disk and returns it as a base64 string.
    """
    import base64
    import os
    
    design = get_active_design(app)
    exportMgr = design.exportManager
    rootComp = design.rootComponent
    
    target = rootComp
    if body_name:
        def get_body(name):
            for i in range(rootComp.bRepBodies.count):
                b = rootComp.bRepBodies.item(i)
                if b.name == name:
                    return b
            raise Exception(f"Body '{name}' not found.")
        target = get_body(body_name)
    
    if file_type.lower() == "step":
        if body_name:
            raise Exception("STEP export currently only supported for the full component in this wrapper.")
        options = exportMgr.createSTEPExportOptions(file_path)
    elif file_type.lower() == "stl":
        options = exportMgr.createSTLExportOptions(target, file_path)
    elif file_type.lower() == "3mf":
        # Note: 3MF export requires Fusion 360 to have the 3MF export feature enabled/available
        try:
            options = exportMgr.create3MFExportOptions(target, file_path)
        except AttributeError:
            # Fallback if create3MFExportOptions is not directly on exportMgr in some older API versions
            raise Exception("3MF export not supported in this version of the Fusion 360 API.")
    else:
        raise Exception("Unsupported file type. Use 'step', 'stl', or '3mf'.")
        
    if not exportMgr.execute(options):
        raise Exception(f"Failed to export {file_type} to {file_path}")
        
    result = {"message": f"Successfully exported model to {file_path}", "file_path": file_path}
    
    if send_to_mcp:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                result["file_content_base64"] = encoded
        else:
            raise Exception("Export succeeded, but file was not found on disk to send to MCP.")
    
    return result

def rename_body(app, old_name, new_name):
    """
    Renames a BRep body.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    for i in range(rootComp.bRepBodies.count):
        body = rootComp.bRepBodies.item(i)
        if body.name == old_name:
            body.name = new_name
            return {"message": f"Renamed body '{old_name}' to '{new_name}'", "new_name": body.name}
            
    raise Exception(f"Body '{old_name}' not found.")

def list_features(app):
    """
    Lists all features in the timeline (root component).
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    features = rootComp.features
    
    features_list = []
    for i in range(features.count):
        feat = features.item(i)
        features_list.append({
            "name": feat.name,
            "type": feat.objectType,
            "index": i,
            "is_suppressed": feat.isSuppressed
        })
    return {"features": features_list}

def rename_feature(app, old_name, new_name):
    """
    Renames a feature in the timeline.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    features = rootComp.features
    
    # Try to find by name
    feat = features.itemByName(old_name)
    if not feat:
        # Fallback manual search if itemByName fails (sometimes API can be picky)
        for i in range(features.count):
            f = features.item(i)
            if f.name == old_name:
                feat = f
                break
                
    if not feat:
        raise Exception(f"Feature '{old_name}' not found.")
        
    feat.name = new_name
    return {"message": f"Renamed feature '{old_name}' to '{new_name}'", "new_name": feat.name}

def rename_sketch(app, old_name, new_name):
    """Renames a sketch."""
    sketch = get_sketch_by_name(app, old_name)
    sketch.name = new_name
    return {"message": f"Renamed sketch '{old_name}' to '{new_name}'", "new_name": sketch.name}

def delete_body(app, body_name):
    """Deletes a BRep body."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    for i in range(rootComp.bRepBodies.count):
        body = rootComp.bRepBodies.item(i)
        if body.name == body_name:
            body.deleteMe()
            return {"message": f"Deleted body '{body_name}'"}
    raise Exception(f"Body '{body_name}' not found.")

def delete_feature(app, feature_name):
    """Deletes a feature from the timeline."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    feat = rootComp.features.itemByName(feature_name)
    if not feat:
        # Manual search
        for i in range(rootComp.features.count):
            f = rootComp.features.item(i)
            if f.name == feature_name:
                feat = f
                break
    if not feat:
        raise Exception(f"Feature '{feature_name}' not found.")
    feat.deleteMe()
    return {"message": f"Deleted feature '{feature_name}'"}

def list_components(app):
    """Lists all sub-components in the design."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    comp_list = []
    # occurrences returns the instances of components in the root
    for i in range(rootComp.occurrences.count):
        occ = rootComp.occurrences.item(i)
        comp = occ.component
        comp_list.append({
            "name": comp.name,
            "occurrence_name": occ.name,
            "is_visible": occ.isVisible
        })
    return {"components": comp_list}

def rename_component(app, old_name, new_name):
    """Renames a sub-component (its underlying component object)."""
    design = get_active_design(app)
    # Search in all components (excluding root potentially, or including)
    for comp in design.allComponents:
        if comp.name == old_name:
            comp.name = new_name
            return {"message": f"Renamed component '{old_name}' to '{new_name}'"}
    raise Exception(f"Component '{old_name}' not found.")

def delete_component(app, occurrence_name):
    """Deletes a component instance (occurrence) from the design."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    occ = rootComp.occurrences.itemByName(occurrence_name)
    if not occ:
        raise Exception(f"Component occurrence '{occurrence_name}' not found in root.")
    occ.deleteMe()
    return {"message": f"Deleted component instance '{occurrence_name}'"}

def list_construction(app):
    """Lists all construction planes, axes, and points."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    planes = []
    for i in range(rootComp.constructionPlanes.count):
        p = rootComp.constructionPlanes.item(i)
        planes.append({"name": p.name, "type": "plane", "is_visible": p.isVisible})
        
    axes = []
    for i in range(rootComp.constructionAxes.count):
        a = rootComp.constructionAxes.item(i)
        axes.append({"name": a.name, "type": "axis", "is_visible": a.isVisible})
        
    points = []
    for i in range(rootComp.constructionPoints.count):
        pt = rootComp.constructionPoints.item(i)
        points.append({"name": pt.name, "type": "point", "is_visible": pt.isVisible})
        
    return {"planes": planes, "axes": axes, "points": points}

def rename_construction(app, old_name, new_name, type="plane"):
    """Renames a construction plane, axis, or point."""
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

def delete_construction(app, name, type="plane"):
    """Deletes a construction plane, axis, or point."""
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

def delete_user_parameter(app, name):
    """Deletes a user parameter."""
    design = get_active_design(app)
    param = design.userParameters.itemByName(name)
    if not param:
        raise Exception(f"User parameter '{name}' not found.")
    param.deleteMe()
    return {"message": f"Deleted parameter '{name}'"}

def compute_all(app):
    """
    Triggers a full rebuild of the design (Compute All).
    """
    design = get_active_design(app)
    design.computeAll()
    # We might want to check health immediately after compute
    return get_design_health(app)

def get_design_health(app):
    """
    Checks the timeline for errors and warnings.
    """
    design = get_active_design(app)
    timeline = design.timeline
    
    issues = []
    # HealthState enums:
    # 0: Success
    # 1: Warning
    # 2: Error
    # 3: Information
    # 4: ErrorButHasLastNativeValue
    # 5: Unknown
    
    for i in range(timeline.count):
        item = timeline.item(i)
        try:
            health = item.healthState
            if health != 0 and health != 3: # Not Success and not Information
                msg = ""
                try:
                    msg = item.errorOrWarningMessage
                except:
                    msg = "Could not retrieve error message."
                
                issues.append({
                    "index": i,
                    "name": item.entity.name if hasattr(item, 'entity') and hasattr(item.entity, 'name') else "Unnamed",
                    "type": item.objectType,
                    "health": health,
                    "message": msg
                })
        except:
            # Skip if we can't query health (likely one of the problematic types: Planes, Sketches, etc.)
            continue
            
    if not issues:
        return {"message": "Design is healthy. No errors or warnings in timeline."}
    else:
        return {
            "message": f"Found {len(issues)} issues in the design timeline.",
            "issues": issues
        }

def _get_timeline_health_map(app):
    """
    Internal helper to get a map of timeline item health.
    Used for detecting new issues after an operation.
    """
    try:
        design = get_active_design(app)
        timeline = design.timeline
        health_map = {}
        for i in range(timeline.count):
            item = timeline.item(i)
            try:
                state = item.healthState
                if state != 0 and state != 3: # Not Success and not Info
                    msg = ""
                    try:
                        msg = item.errorOrWarningMessage
                    except:
                        pass
                    # Use a stable-ish key: index + type
                    health_map[i] = (item.objectType, state, msg)
            except:
                continue
        return health_map
    except:
        return {}

def list_materials(app):
    """
    Lists available physical materials in the design and favorite libraries.
    """
    design = get_active_design(app)
    materials = []
    
    # Check design materials
    for i in range(design.materials.count):
        m = design.materials.item(i)
        materials.append({"name": m.name, "library": "Design"})
    
    # Check favorite libraries
    # Fusion 360 Material Library is usually always present
    lib = app.materialLibraries.itemByName("Fusion 360 Material Library")
    if lib:
        for i in range(lib.materials.count):
            m = lib.materials.item(i)
            materials.append({"name": m.name, "library": lib.name})
            if len(materials) > 100: # Limit output
                break
                
    return {"materials": materials}

def apply_material(app, body_name, material_name):
    """
    Sets the physical material of a body.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    
    # Check design first
    material = design.materials.itemByName(material_name)
    
    # Check libraries if not in design
    if not material:
        lib = app.materialLibraries.itemByName("Fusion 360 Material Library")
        if lib:
            material = lib.materials.itemByName(material_name)
            
    if not material:
        raise Exception(f"Material '{material_name}' not found.")
        
    body.material = material
    return {"message": f"Successfully applied material '{material_name}' to body '{body_name}'."}

def list_appearances(app):
    """
    Lists available appearances in the design and favorite libraries.
    """
    design = get_active_design(app)
    appearances = []
    
    # Check design appearances
    for i in range(design.appearances.count):
        a = design.appearances.item(i)
        appearances.append({"name": a.name, "library": "Design"})
        
    # Check favorite libraries
    lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
    if lib:
        for i in range(lib.appearances.count):
            a = lib.appearances.item(i)
            appearances.append({"name": a.name, "library": lib.name})
            if len(appearances) > 100: # Limit output
                break
                
    return {"appearances": appearances}

def apply_appearance(app, body_name, appearance_name):
    """
    Sets the visual appearance of a body.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    def get_body(name):
        for i in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(i)
            if b.name == name:
                return b
        raise Exception(f"Body '{name}' not found.")
        
    body = get_body(body_name)
    
    # Check design first
    appearance = design.appearances.itemByName(appearance_name)
    
    # Check libraries if not in design
    if not appearance:
        lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
        if lib:
            appearance = lib.appearances.itemByName(appearance_name)
            
    if not appearance:
        raise Exception(f"Appearance '{appearance_name}' not found.")
        
    body.appearance = appearance
    return {"message": f"Successfully applied appearance '{appearance_name}' to body '{body_name}'."}

def start_timeline_group(app, name):
    """Starts a timeline group. All operations until stop_timeline_group will be grouped."""
    design = get_active_design(app)
    _group_stack.append({"name": name, "start": design.timeline.count})
    return {"message": f"Started timeline group '{name}'"}

def stop_timeline_group(app):
    """Stops the current timeline group and creates it in Fusion 360."""
    design = get_active_design(app)
    if not _group_stack:
        raise Exception("No active timeline group to stop.")
    
    group_info = _group_stack.pop()
    start_idx = group_info["start"]
    end_idx = design.timeline.count - 1
    
    if end_idx >= start_idx:
        group = design.timeline.timelineGroups.add(start_idx, end_idx)
        group.name = group_info["name"]
        return {"message": f"Created timeline group '{group.name}' with {end_idx - start_idx + 1} items."}
    else:
        return {"message": f"Timeline group '{group_info['name']}' was empty and not created."}
