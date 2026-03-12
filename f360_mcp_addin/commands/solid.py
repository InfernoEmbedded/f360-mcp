import adsk.core
import adsk.fusion
import math
from . import command
from .base import get_active_design, get_sketch_by_name, _get_body
from .sketch import resolve_entity

@command()
def create_extrude(app, sketch_name, distance, operation="new_body", profile_index=0):
    """
    Extrudes a sketch profile.
    
    Arguments:
        distance (float): Extrusion depth in cm.
        operation (str): new_body, join, cut, intersect.
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
    distance_val = adsk.core.ValueInput.createByReal(distance)
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

@command()
def create_revolve(app, sketch_name, axis_ent_type, axis_ent_idx, angle, operation="new_body", profile_index=0):
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

@command()
def create_sweep(app, profile_sketch_name, path_sketch_name, path_ent_type, path_ent_idx, operation="new_body", profile_index=0):
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

@command()
def create_loft(app, profiles_info):
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

@command()
def create_hole(app, sketch_name, point_idx, diameter, depth):
    """Creates a circular hole. Units: cm."""
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

@command()
def create_shell(app, body_name, thickness):
    """Hollows a body. Units: cm."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    shells = rootComp.features.shellFeatures
    body = _get_body(app, body_name)
    entities = adsk.core.ObjectCollection.create()
    entities.add(body)
    thickness_val = adsk.core.ValueInput.createByReal(thickness)
    shellInput = shells.createInput(entities, False)
    shellInput.insideThickness = thickness_val
    shell = shells.add(shellInput)
    return {"message": f"Shell created with {thickness}cm thickness.", "feature_name": shell.name}

@command()
def create_fillet(app, body_name, radius):
    """Fillets all edges of a body. Units: cm."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    fillets = rootComp.features.filletFeatures
    body = _get_body(app, body_name)
    edges = adsk.core.ObjectCollection.create()
    for i in range(body.edges.count):
        edges.add(body.edges.item(i))
    radius_val = adsk.core.ValueInput.createByReal(radius)
    filletInput = fillets.createInput()
    filletInput.addConstantRadiusEdgeSet(edges, radius_val, True)
    fillet = fillets.add(filletInput)
    return {"message": f"Filleted all edges of body {body_name} with {radius}cm radius.", "feature_name": fillet.name}

@command()
def create_chamfer(app, body_name, distance):
    """Chamfers all edges of a body. Units: cm."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    chamfers = rootComp.features.chamferFeatures
    body = _get_body(app, body_name)
    edges = adsk.core.ObjectCollection.create()
    for i in range(body.edges.count):
        edges.add(body.edges.item(i))
    distance_val = adsk.core.ValueInput.createByReal(distance)
    chamferInput = chamfers.createInput(edges, True)
    chamferInput.setToEqualDistance(distance_val)
    chamfer = chamfers.add(chamferInput)
    return {"message": f"Chamfered all edges of body {body_name} with {distance}cm distance.", "feature_name": chamfer.name}

@command()
def feature_mirror(app, body_name, plane_name):
    design = get_active_design(app)
    rootComp = design.rootComponent
    mirrors = rootComp.features.mirrorFeatures
    body = _get_body(app, body_name)
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

@command()
def create_rectangular_pattern(app, body_name, count_x, count_y, distance_x, distance_y):
    design = get_active_design(app)
    rootComp = design.rootComponent
    body = _get_body(app, body_name)
    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)
    xAxis = rootComp.xConstructionAxis
    yAxis = rootComp.yConstructionAxis
    rectPatterns = rootComp.features.rectangularPatternFeatures
    rectPatternInput = rectPatterns.createInput(inputEntities, xAxis, adsk.core.ValueInput.createByReal(count_x), adsk.core.ValueInput.createByReal(distance_x), adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    rectPatternInput.setDirectionTwo(yAxis, adsk.core.ValueInput.createByReal(count_y), adsk.core.ValueInput.createByReal(distance_y))
    pattern = rectPatterns.add(rectPatternInput)
    return {"message": f"Created rectangular pattern for '{body_name}'", "pattern_name": pattern.name}

@command()
def create_circular_pattern(app, body_name, axis_name, count, angle_deg):
    design = get_active_design(app)
    rootComp = design.rootComponent
    body = _get_body(app, body_name)
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
    circPatternInput.angle = adsk.core.ValueInput.createByReal(math.radians(angle_deg))
    circPatternInput.isSymmetric = False
    pattern = circPatterns.add(circPatternInput)
    return {"message": f"Created circular pattern for '{body_name}' around {axis_name}", "pattern_name": pattern.name}

@command()
def list_bodies(app):
    design = get_active_design(app)
    bodies_list = []
    # Include all bodies from all components
    for comp in design.allComponents:
        for i in range(comp.bRepBodies.count):
            body = comp.bRepBodies.item(i)
            bodies_list.append({"name": body.name, "component": comp.name})
    return {"bodies": bodies_list}

@command()
def combine_bodies(app, target_body_name, tool_body_names, operation="join"):
    design = get_active_design(app)
    rootComp = design.rootComponent
    combines = rootComp.features.combineFeatures
    target = _get_body(app, target_body_name)
    tools = adsk.core.ObjectCollection.create()
    for t_name in tool_body_names:
        tools.add(_get_body(app, t_name))
    combineInput = combines.createInput(target, tools)
    op_map = {
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation
    }
    combineInput.operation = op_map.get(operation.lower(), adsk.fusion.FeatureOperations.JoinFeatureOperation)
    combine = combines.add(combineInput)
    return {"message": f"Combined bodies using {operation}.", "feature_name": combine.name}

@command()
def rename_body(app, old_name, new_name):
    body = _get_body(app, old_name)
    body.name = new_name
    return {"message": f"Renamed body '{old_name}' to '{new_name}'", "new_name": body.name}

@command()
def delete_body(app, body_name):
    body = _get_body(app, body_name)
    body.deleteMe()
    return {"message": f"Deleted body '{body_name}'"}

@command()
def list_features(app):
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

@command()
def rename_feature(app, old_name, new_name):
    design = get_active_design(app)
    rootComp = design.rootComponent
    feat = rootComp.features.itemByName(old_name)
    if not feat:
        for i in range(rootComp.features.count):
            f = rootComp.features.item(i)
            if f.name == old_name:
                feat = f
                break
    if not feat:
        raise Exception(f"Feature '{old_name}' not found.")
    feat.name = new_name
    return {"message": f"Renamed feature '{old_name}' to '{new_name}'", "new_name": feat.name}

@command()
def delete_feature(app, feature_name):
    design = get_active_design(app)
    rootComp = design.rootComponent
    feat = rootComp.features.itemByName(feature_name)
    if not feat:
        for i in range(rootComp.features.count):
            f = rootComp.features.item(i)
            if f.name == feature_name:
                feat = f
                break
    if not feat:
        raise Exception(f"Feature '{feature_name}' not found.")
    feat.deleteMe()
    return {"message": f"Deleted feature '{feature_name}'"}

@command()
def compute_all(app):
    design = get_active_design(app)
    design.computeAll()
    return {"message": "Computed all features (forced rebuild)."}

@command()
def get_design_health(app):
    design = get_active_design(app)
    rootComp = design.rootComponent
    features = rootComp.features
    errors = 0
    warnings = 0
    total = features.count
    for i in range(total):
        feat = features.item(i)
        if feat.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
            errors += 1
        elif feat.healthState == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
            warnings += 1
    return {
        "design_name": design.rootComponent.name,
        "total_features": total,
        "errors": errors,
        "warnings": warnings,
        "is_healthy": (errors == 0 and warnings == 0)
    }
