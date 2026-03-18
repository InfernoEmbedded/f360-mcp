import adsk.core
import adsk.fusion
from . import command
from .base import get_active_design, get_sketch_by_name

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
    elif base_type == "axis":
        comp = sketch.parentComponent
        if index == 0:
            return comp.xConstructionAxis
        if index == 1:
            return comp.yConstructionAxis
        if index == 2:
            return comp.zConstructionAxis
        axis_index = index - 3
        if axis_index >= 0 and axis_index < comp.constructionAxes.count:
            return comp.constructionAxes.item(axis_index)
    elif base_type == "construction" and sub_type == "axis":
        comp = sketch.parentComponent
        if index >= 0 and index < comp.constructionAxes.count:
            return comp.constructionAxes.item(index)
        
    if ent:
        return ent
    raise Exception(f"Unable to resolve entity: {entity_type} at index {index}")

@command()
def create_sketch(app, name, plane_name="XY", body_name=None, face_index=None):
    """
    Creates a new sketch on a plane or face.
    
    Arguments:
        name (str): Mandatory name for the new sketch.
        plane_name (str): "XY", "XZ", "YZ", or construction plane name.
        body_name (str): Optional. Name of the body if sketching on a face.
        face_index (int): Optional. Index of the face on the body.
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    
    if body_name is not None and face_index is not None:
        from .base import _get_body
        body = _get_body(app, body_name)
        if face_index < 0 or face_index >= body.faces.count:
            raise Exception(f"Face index {face_index} out of bounds.")
        planes = body.faces.item(face_index)
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
        
    sketches = rootComp.sketches
    sketch = sketches.add(planes)
    sketch.name = name
    
    return {"sketch_name": sketch.name, "message": "Sketch created successfully"}

@command()
def create_sketch_on_plane(app, name, plane_name):
    """Compatibility wrapper for explicit plane-name sketch creation."""
    return create_sketch(app, name, plane_name=plane_name)

@command()
def add_circle(app, sketch_name, x, y, radius):
    """Adds a circle. Units: cm."""
    sketch = get_sketch_by_name(app, sketch_name)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(x, y, 0)
    circle = circles.addByCenterRadius(center, radius)
    return {"message": f"Circle added at ({x},{y}) with radius {radius}"}

@command()
def add_line(app, sketch_name, x1, y1, x2, y2):
    """Adds a line. Units: cm."""
    sketch = get_sketch_by_name(app, sketch_name)
    lines = sketch.sketchCurves.sketchLines
    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    line = lines.addByTwoPoints(p1, p2)
    return {"message": f"Line added from ({x1},{y1}) to ({x2},{y2})"}

@command()
def add_rectangle(app, sketch_name, x1, y1, x2, y2, x3=None, y3=None, rect_type="two_point"):
    sketch = get_sketch_by_name(app, sketch_name)
    lines = sketch.sketchCurves.sketchLines
    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    
    if rect_type == "three_point" and x3 is not None and y3 is not None:
        p3 = adsk.core.Point3D.create(x3, y3, 0)
        lines.addThreePointRectangle(p1, p2, p3)
        return {"message": "Three-point rectangle added."}
    elif rect_type == "center":
        lines.addCenterPointRectangle(p1, p2)
        return {"message": "Center-point rectangle added."}
    else:
        lines.addTwoPointRectangle(p1, p2)
        return {"message": "Two-point rectangle added."}

@command()
def add_arc(app, sketch_name, x1, y1, x2, y2, x3, y3, arc_type="three_point"):
    sketch = get_sketch_by_name(app, sketch_name)
    arcs = sketch.sketchCurves.sketchArcs
    if arc_type == "center_start_sweep":
        center = adsk.core.Point3D.create(x1, y1, 0)
        start = adsk.core.Point3D.create(x2, y2, 0)
        sweep = x3
        arcs.addByCenterStartSweep(center, start, sweep)
        return {"message": "Center-start-sweep arc added."}
    else:
        p1 = adsk.core.Point3D.create(x1, y1, 0)
        p2 = adsk.core.Point3D.create(x2, y2, 0)
        p3 = adsk.core.Point3D.create(x3, y3, 0)
        arcs.addByThreePoints(p1, p2, p3)
        return {"message": "Three-point arc added."}

@command()
def add_spline(app, sketch_name, points):
    sketch = get_sketch_by_name(app, sketch_name)
    splines = sketch.sketchCurves.sketchFittedSplines
    points_collection = adsk.core.ObjectCollection.create()
    for pt in points:
        points_collection.add(adsk.core.Point3D.create(pt[0], pt[1], 0))
    splines.add(points_collection)
    return {"message": f"Spline added with {len(points)} points."}

@command()
def add_polygon(app, sketch_name, center_x, center_y, num_sides, vertex_x, vertex_y, poly_type="inscribed"):
    """Adds a regular polygon. Units: cm."""
    sketch = get_sketch_by_name(app, sketch_name)
    polygons = sketch.sketchPolygons
    center = adsk.core.Point3D.create(center_x, center_y, 0)
    vertex = adsk.core.Point3D.create(vertex_x, vertex_y, 0)
    if poly_type == "circumscribed":
        polygons.addCircumscribedPolygon(center, num_sides, vertex)
    else:
        polygons.addInscribedPolygon(center, num_sides, vertex)
    return {"message": f"{poly_type.capitalize()} polygon with {num_sides} sides added."}

@command()
def add_ellipse(app, sketch_name, center_x, center_y, major_x, major_y, minor_x, minor_y):
    sketch = get_sketch_by_name(app, sketch_name)
    ellipses = sketch.sketchCurves.sketchEllipses
    center = adsk.core.Point3D.create(center_x, center_y, 0)
    major = adsk.core.Point3D.create(major_x, major_y, 0)
    minor = adsk.core.Point3D.create(minor_x, minor_y, 0)
    ellipses.add(center, major, minor)
    return {"message": "Ellipse added."}

@command()
def add_point(app, sketch_name, x, y):
    sketch = get_sketch_by_name(app, sketch_name)
    points = sketch.sketchPoints
    p = adsk.core.Point3D.create(x, y, 0)
    points.add(p)
    return {"message": f"Point added at ({x}, {y})."}

@command()
def add_text(app, sketch_name, text, x, y, height=0.5):
    sketch = get_sketch_by_name(app, sketch_name)
    texts = sketch.sketchTexts
    position = adsk.core.Point3D.create(x, y, 0)
    input = texts.createInput(text, height, position)
    texts.add(input)
    return {"message": f"Text '{text}' added at ({x}, {y})."}

@command()
def apply_constraint(app, sketch_name, constraint_type, ent1_type, ent1_idx, ent2_type=None, ent2_idx=None):
    """
    Applies a geometric constraint.
    
    Types: coincident, collinear, concentric, midpoint, parallel, perpendicular, 
           horizontal, vertical, tangent, equal.
    """
    sketch = get_sketch_by_name(app, sketch_name)
    constraints = sketch.geometricConstraints
    e1 = resolve_entity(sketch, ent1_type, ent1_idx)
    e2 = resolve_entity(sketch, ent2_type, ent2_idx) if ent2_type else None
    
    if constraint_type == "coincident":
        constraints.addCoincident(e1, e2)
    elif constraint_type == "collinear":
        constraints.addCollinear(e1, e2)
    elif constraint_type == "concentric":
        constraints.addConcentric(e1, e2)
    elif constraint_type == "midpoint":
        constraints.addMidPoint(e1, e2)
    elif constraint_type == "parallel":
        constraints.addParallel(e1, e2)
    elif constraint_type == "perpendicular":
        constraints.addPerpendicular(e1, e2)
    elif constraint_type == "horizontal":
        if e2: constraints.addHorizontalPoints(e1, e2)
        else: constraints.addHorizontal(e1)
    elif constraint_type == "vertical":
        if e2: constraints.addVerticalPoints(e1, e2)
        else: constraints.addVertical(e1)
    elif constraint_type == "tangent":
        constraints.addTangent(e1, e2)
    elif constraint_type == "equal":
        constraints.addEqual(e1, e2)
    else:
        raise Exception(f"Unknown constraint type: {constraint_type}")
    return {"message": f"Successfully added {constraint_type} constraint."}

@command()
def add_symmetry_constraint(app, sketch_name, ent1_type, ent1_idx, ent2_type, ent2_idx, sym_line_type, sym_line_idx):
    sketch = get_sketch_by_name(app, sketch_name)
    constraints = sketch.geometricConstraints
    e1 = resolve_entity(sketch, ent1_type, ent1_idx)
    e2 = resolve_entity(sketch, ent2_type, ent2_idx)
    sym_line = resolve_entity(sketch, sym_line_type, sym_line_idx)
    constraints.addSymmetry(e1, e2, sym_line)
    return {"message": "Successfully added symmetry constraint."}

@command()
def add_distance_dimension(app, sketch_name, ent1_type, ent1_idx, ent2_type, ent2_idx, text_x, text_y, orientation="aligned"):
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

@command()
def add_radial_dimension(app, sketch_name, ent_type, ent_idx, text_x, text_y):
    sketch = get_sketch_by_name(app, sketch_name)
    dims = sketch.sketchDimensions
    e1 = resolve_entity(sketch, ent_type, ent_idx)
    text_pos = adsk.core.Point3D.create(text_x, text_y, 0)
    dim = dims.addRadialDimension(e1, text_pos)
    return {"message": "Radial dimension added.", "value": dim.parameter.value}

@command()
def add_diameter_dimension(app, sketch_name, ent_type, ent_idx, text_x, text_y):
    sketch = get_sketch_by_name(app, sketch_name)
    dims = sketch.sketchDimensions
    e1 = resolve_entity(sketch, ent_type, ent_idx)
    text_pos = adsk.core.Point3D.create(text_x, text_y, 0)
    dim = dims.addDiameterDimension(e1, text_pos)
    return {"message": "Diameter dimension added.", "value": dim.parameter.value}

@command()
def add_angular_dimension(app, sketch_name, line1_idx, line2_idx, text_x, text_y):
    sketch = get_sketch_by_name(app, sketch_name)
    dims = sketch.sketchDimensions
    line1 = resolve_entity(sketch, "line", line1_idx)
    line2 = resolve_entity(sketch, "line", line2_idx)
    text_pos = adsk.core.Point3D.create(text_x, text_y, 0)
    dim = dims.addAngularDimension(line1, line2, text_pos)
    return {"message": "Angular dimension added.", "value": dim.parameter.value}

@command()
def list_sketches(app):
    design = get_active_design(app)
    # Search all components for sketches
    sketch_list = []
    for comp in design.allComponents:
        for sketch in comp.sketches:
            sketch_list.append({"name": sketch.name, "component": comp.name})
    return {"sketches": sketch_list}

@command()
def delete_sketch(app, sketch_name):
    sketch = get_sketch_by_name(app, sketch_name)
    sketch.deleteMe()
    return {"message": f"Sketch '{sketch_name}' deleted."}

@command()
def project_geometry(app, sketch_name, ent_type, ent_idx, from_sketch_name=None):
    target_sketch = get_sketch_by_name(app, sketch_name)
    source_sketch = get_sketch_by_name(app, from_sketch_name) if from_sketch_name else target_sketch
    ent = resolve_entity(source_sketch, ent_type, ent_idx)
    projected_curves = target_sketch.project(ent)
    return {"message": f"Projected {len(projected_curves)} curves."}

@command()
def offset_geometry(app, sketch_name, ent_type, ent_idx, offset_distance):
    sketch = get_sketch_by_name(app, sketch_name)
    ent = resolve_entity(sketch, ent_type, ent_idx)
    curves = adsk.core.ObjectCollection.create()
    curves.add(ent)
    dir_point = adsk.core.Point3D.create(0, 0, 0)
    offset_curves = sketch.offset(curves, dir_point, offset_distance)
    return {"message": f"Created offset with {len(offset_curves)} curves."}

@command()
def delete_sketch_entity(app, sketch_name, ent_type, ent_idx):
    sketch = get_sketch_by_name(app, sketch_name)
    ent = resolve_entity(sketch, ent_type, ent_idx)
    ent.deleteMe()
    return {"message": f"Entity '{ent_type}' at index {ent_idx} deleted."}

@command()
def trim_sketch_geometry(app, sketch_name, ent_type, ent_idx, x, y):
    sketch = get_sketch_by_name(app, sketch_name)
    ent = resolve_entity(sketch, ent_type, ent_idx)
    pt = adsk.core.Point3D.create(x, y, 0)
    if hasattr(ent, 'trim'):
        new_curves = ent.trim(pt)
        count = new_curves.count if new_curves else 0
        return {"message": f"Trimmed curve resulting in {count} new pieces."}
    else:
        raise Exception(f"Entity type {ent_type} does not support trimming.")
