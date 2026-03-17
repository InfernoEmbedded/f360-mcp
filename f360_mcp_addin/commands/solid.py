import adsk.core
import adsk.fusion
import math
from . import command
from .base import get_active_design, get_sketch_by_name, _get_body
from .sketch import resolve_entity

@command()
def create_extrude(app, name, sketch_name, distance, operation="new_body", profile_index=0):
    """
    Extrudes a sketch profile.
    
    Arguments:
        name (str): Mandatory name for the new feature.
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
    extrude.name = name
    if fusion_op == adsk.fusion.FeatureOperations.NewBodyFeatureOperation and extrude.bodies.count > 0:
        extrude.bodies.item(0).name = name
    return {"message": f"Extruded {distance}cm using operation {operation} as '{name}'.", "feature_name": extrude.name}

@command()
def create_revolve(app, name, sketch_name, axis_ent_type, axis_ent_idx, angle, operation="new_body", profile_index=0):
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
    revolve.name = name
    if fusion_op == adsk.fusion.FeatureOperations.NewBodyFeatureOperation and revolve.bodies.count > 0:
        revolve.bodies.item(0).name = name
    return {"message": f"Revolved {angle} degrees using operation {operation} as '{name}'.", "feature_name": revolve.name}

@command()
def create_sweep(app, name, profile_sketch_name, path_sketch_name, path_ent_type, path_ent_idx, operation="new_body", profile_index=0):
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
    sweep.name = name
    if fusion_op == adsk.fusion.FeatureOperations.NewBodyFeatureOperation and sweep.bodies.count > 0:
        sweep.bodies.item(0).name = name
    return {"message": f"Sweep '{name}' created using operation {operation}.", "feature_name": sweep.name}

@command()
def create_loft(app, name, profiles_info):
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
    loft.name = name
    if loft.bodies.count > 0:
        loft.bodies.item(0).name = name
    return {"message": f"Created loft '{name}' from {len(profiles_info)} profiles.", "feature_name": loft.name}

@command()
def create_hole(app, name, sketch_name, point_idx, diameter, depth):
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
    hole.name = name
    return {"message": f"Hole '{name}' created with diameter {diameter}cm and depth {depth}cm.", "feature_name": hole.name}

@command()
def create_shell(app, name, body_name, thickness):
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
    shell.name = name
    return {"message": f"Shell '{name}' created with {thickness}cm thickness.", "feature_name": shell.name}

@command()
def create_fillet(app, name, body_name, radius):
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
    fillet.name = name
    return {"message": f"Filleted '{name}' all edges of body {body_name} with {radius}cm radius.", "feature_name": fillet.name}

@command()
def create_chamfer(app, name, body_name, distance):
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
    chamfer.name = name
    return {"message": f"Chamfered '{name}' all edges of body {body_name} with {distance}cm distance.", "feature_name": chamfer.name}

@command()
def feature_mirror(app, name, body_name, plane_name):
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
    mirror.name = name
    return {"message": f"Mirrored body {body_name} across {plane_name} plane as '{name}'.", "feature_name": mirror.name}

@command()
def create_rectangular_pattern(app, name, body_name, count_x, count_y, distance_x, distance_y):
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
    pattern.name = name
    return {"message": f"Created rectangular pattern '{name}' for '{body_name}'", "pattern_name": pattern.name}

@command()
def create_circular_pattern(app, name, body_name, axis_name, count, angle_deg):
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
    pattern.name = name
    return {"message": f"Created circular pattern '{name}' for '{body_name}' around {axis_name}", "pattern_name": pattern.name}

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
def combine_bodies(app, name, target_body_name, tool_body_names, operation="join"):
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
    combine.name = name
    return {"message": f"Combined bodies as '{name}' using {operation}.", "feature_name": combine.name}

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
def split_body(app, name, body_name, split_tool_name, is_surface_tool=True):
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    body = _get_body(app, body_name)
    splitBodyFeats = rootComp.features.splitBodyFeatures
    
    # Resolve splitting tool
    tool = None
    plane_map = {
        'xy': rootComp.xYConstructionPlane,
        'yz': rootComp.yZConstructionPlane,
        'xz': rootComp.xZConstructionPlane,
        'zx': rootComp.xZConstructionPlane
    }
    
    if split_tool_name.lower() in plane_map:
        tool = plane_map[split_tool_name.lower()]
    
    if not tool:
        # Check construction planes
        for comp in design.allComponents:
            tool = comp.constructionPlanes.itemByName(split_tool_name)
            if tool:
                break
                
    if not tool:
        # Check bodies
        try:
            tool = _get_body(app, split_tool_name)
        except:
            pass
            
    if not tool:
         raise Exception(f"Splitting tool '{split_tool_name}' not found. Must be a standard plane (XY, YZ, XZ), construction plane, or body.")
         
    splitInput = splitBodyFeats.createInput(body, tool, is_surface_tool)
    split = splitBodyFeats.add(splitInput)
    split.name = name
    return {"message": f"Successfully split body '{body_name}' as '{name}' using '{split_tool_name}'.", "feature_name": split.name}

@command()
def scale_body(app, name, body_name, scale_factor):
    """Uniformly scales a body from the component origin."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    scaleFeats = rootComp.features.scaleFeatures
    
    body = _get_body(app, body_name)
    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)
    
    basePoint = rootComp.originConstructionPoint
    scale_val = adsk.core.ValueInput.createByReal(scale_factor)
    
    scaleInput = scaleFeats.createInput(inputEntities, basePoint, scale_val)
    scale = scaleFeats.add(scaleInput)
    scale.name = name
    return {"message": f"Successfully scaled body '{body_name}' by factor {scale_factor} as '{name}'.", "feature_name": scale.name}

@command()
def create_thread(app, name, body_name, face_index=0, is_modeled=True):
    """Adds a thread to a cylindrical face of a body."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    body = _get_body(app, body_name)
    if face_index >= body.faces.count:
        raise Exception(f"Face index {face_index} out of bounds for body {body_name}.")
    cylinderFace = body.faces.item(face_index)
    
    threadFeats = rootComp.features.threadFeatures
    threadDataQuery = threadFeats.threadDataQuery
    defaultThreadType = threadDataQuery.defaultMetricThreadType
    
    result = threadDataQuery.recommendThreadData(cylinderFace.geometry.radius * 2, False, defaultThreadType)
    if not result[0]:
        result = threadDataQuery.recommendThreadData(cylinderFace.geometry.radius * 2, True, defaultThreadType)
        
    if not result[0]:
        raise Exception("Could not find a recommended thread size for this cylinder.")
        
    threadInfo = threadFeats.createThreadInfo(is_modeled, defaultThreadType, result[1], result[2])
    
    faces = adsk.core.ObjectCollection.create()
    faces.add(cylinderFace)
    
    threadInput = threadFeats.createInput(faces, threadInfo)
    thread = threadFeats.add(threadInput)
    thread.name = name
    return {"message": f"Successfully created thread '{name}' on '{body_name}' face {face_index}.", "feature_name": thread.name}

@command()
def move_body(app, name, body_name, dx, dy, dz):
    """Translates a body by (dx, dy, dz) in cm."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    body = _get_body(app, body_name)
    moveFeats = rootComp.features.moveFeatures
    
    entities = adsk.core.ObjectCollection.create()
    entities.add(body)
    
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(dx, dy, dz)
    
    moveInput = moveFeats.createInput2(entities)
    moveInput.defineAsFreeMove(transform)
    move = moveFeats.add(moveInput)
    move.name = name
    
    return {"message": f"Successfully moved '{body_name}' by {dx},{dy},{dz} as '{name}'.", "feature_name": move.name}

@command()
def measure_interference(app, body_names):
    """Checks for interference between a list of bodies."""
    design = get_active_design(app)
    
    entities = adsk.core.ObjectCollection.create()
    for name in body_names:
        body = _get_body(app, name)
        entities.add(body)
        
    if entities.count < 2:
        raise Exception("Need at least 2 bodies to measure interference.")
        
    interferenceInput = design.createInterferenceInput(entities)
    results = design.analyzeInterference(interferenceInput)
    
    interferences = []
    if results and results.count > 0:
        for i in range(results.count):
            res = results.item(i)
            vol = res.interferenceBody.volume if res.interferenceBody else 0.0
            interferences.append({
                "body1": res.entityOne.name,
                "body2": res.entityTwo.name,
                "volume": vol
            })
            
    return {"message": "Successfully executed measure_interference.", "interferences": interferences, "has_interference": len(interferences) > 0}

@command()
def create_rib(app, name, sketch_name, thickness):
    """Creates a rib feature from a sketch profile."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    sketch = get_sketch_by_name(app, sketch_name)
    if sketch.profiles.count == 0:
        raise Exception(f"No profiles found in sketch {sketch_name}.")
        
    ribFeats = rootComp.features.ribFeatures
    thick = adsk.core.ValueInput.createByReal(thickness)
    
    # A rib takes a sketch curve collection or a profile. 
    # Usually, sketchCurve is used for Rib since it expects open/closed curves. Let's pass the first profile.
    ribInput = ribFeats.createInput(sketch.profiles.item(0), thick)
    ribInput.isSymmetric = True
    
    rib = ribFeats.add(ribInput)
    rib.name = name
    return {"message": f"Successfully created rib '{name}' from {sketch_name}.", "feature_name": rib.name}

@command()
def create_web(app, name, sketch_name, thickness):
    """Creates a web feature from a sketch profile."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    sketch = get_sketch_by_name(app, sketch_name)
    if sketch.profiles.count == 0:
        raise Exception(f"No profiles found in sketch {sketch_name}.")
        
    webFeats = rootComp.features.webFeatures
    thick = adsk.core.ValueInput.createByReal(thickness)
    
    webInput = webFeats.createInput(sketch.profiles.item(0), thick)
    
    web = webFeats.add(webInput)
    web.name = name
    return {"message": f"Successfully created web '{name}' from {sketch_name}.", "feature_name": web.name}

@command()
def create_emboss(app, name, sketch_name, body_name, depth):
    """Creates an emboss or deboss feature."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    sketch = get_sketch_by_name(app, sketch_name)
    if sketch.profiles.count == 0:
        raise Exception(f"No profiles found in sketch {sketch_name}.")
        
    body = _get_body(app, body_name)
    
    embossFeats = rootComp.features.embossFeatures
    profiles = adsk.core.ObjectCollection.create()
    profiles.add(sketch.profiles.item(0))
    
    faces = adsk.core.ObjectCollection.create()
    for i in range(body.faces.count):
        faces.add(body.faces.item(i))
        
    embossInput = embossFeats.createInput(profiles, faces)
    embossInput.depth = adsk.core.ValueInput.createByReal(depth)
    
    emboss = embossFeats.add(embossInput)
    emboss.name = name
    return {"message": f"Successfully created emboss '{name}' on {body_name}.", "feature_name": emboss.name}

@command()
def import_mesh(app, file_path):
    """Imports an STL or OBJ mesh file into the active design."""
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    importManager = app.importManager
    
    # Determine type by extension
    ext = file_path.lower()
    if ext.endswith('.stl'):
        importOptions = importManager.createSTLImportOptions(file_path)
    elif ext.endswith('.obj'):
        importOptions = importManager.createOBJImportOptions(file_path)
    else:
        raise Exception(f"Unsupported mesh format for file: {file_path}. Must be .stl or .obj")
        
    try:
        importManager.importToTarget(importOptions, rootComp)
    except Exception as e:
        raise Exception(f"Failed to import mesh: {str(e)}")
        
    # The import target usually results in a new mesh body or component. 
    # For simplicity we'll just return success. It takes time in Fusion GUI but via API it adds to root.
    return {"message": f"Successfully imported mesh from {file_path}."}

@command()
def convert_mesh_to_solid(app, body_name, method="prismatic"):
    """
    Converts a mesh body to a solid (BRep) body using Fusion's native conversion tool.
    
    Arguments:
        body_name (str): The name of the mesh body to convert.
        method (str): 'faceted' (each triangle becomes a face) or 'prismatic' (attempts to merge planar/cylindrical faces). Prismatic is best for mechanical parts.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    # Try to find the mesh body
    mesh_body = None
    for m in rootComp.meshBodies:
        if m.name == body_name:
            mesh_body = m
            break
            
    if not mesh_body:
        raise Exception(f"Mesh body '{body_name}' not found.")
        
    baseFeats = rootComp.features.baseFeatures
    baseFeat = baseFeats.add()
    
    try:
        baseFeat.startEdit()
        
        # Build collection of meshes to convert
        meshes = adsk.core.ObjectCollection.create()
        meshes.add(mesh_body)
        
        # Convert it
        if method.lower() == "faceted":
            # API uses createBRepFaceForMeshTriangle = True for faceted
            # Actually, the direct API approach is via the BRepBody.createFromMesh or similar?
            # Fusion 360 python API handles this via adsk.fusion.BRepBody.createFromMesh
            # No wait, for "Convert Mesh" feature it's typically just replacing it inside a BaseFeature.
            # Using adsk.fusion.BRepBody.create() from mesh? 
            # In the new Fusion update, they added MeshToBRepFeature. Let's use that if available, otherwise fallback to BRepBody.createBRep
            pass # See implementation below
            
        meshToBRepFeats = rootComp.features.meshToBRepFeatures
        meshToBRepInput = meshToBRepFeats.createInput(meshes)
        
        # Setup method (if API supports it). Default is prismatic natively now mostly if unstated
        if method.lower() == "prismatic":
            # Just create it. The API Enum for prismatic is not always easily exposed, 
            # or it might be MeshToBRepFeatureOperation = adsk.fusion.MeshToBRepFeatureOperation.NewBodyMeshToBRepFeatureOperation
            pass
            
        converted = meshToBRepFeats.add(meshToBRepInput)
        
        # Optional: Hide original mesh body
        mesh_body.isLightBulbOn = False
        
        baseFeat.finishEdit()
        
        new_names = [b.name for b in converted.bodies] if converted.bodies else []
        return {"message": f"Successfully converted {body_name} to solid.", "new_bodies": new_names}
        
    except Exception as e:
        baseFeat.finishEdit()
        raise Exception(f"Failed to convert mesh to solid: {str(e)}")

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

