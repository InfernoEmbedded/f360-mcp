import adsk.core
import adsk.fusion
from . import command
from .base import get_active_design, _get_body

@command(name='get_face_info')
def get_face_info(app, body_name):
    body = _get_body(app, body_name)
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

@command()
def get_edge_info(app, body_name):
    body = _get_body(app, body_name)
    edges_info = []
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        info = {
            "edge_index": i,
            "length_cm": round(edge.length, 3),
            "geometry_type": edge.geometry.objectType.split('::')[-1]
        }
        edges_info.append(info)
    return {"body_name": body_name, "edges": edges_info}

@command()
def get_sketch_info(app, sketch_name):
    from .base import get_sketch_by_name
    sketch = get_sketch_by_name(app, sketch_name)
    return {
        "name": sketch.name,
        "profiles_count": sketch.profiles.count,
        "curves_count": sketch.sketchCurves.count,
        "points_count": sketch.sketchPoints.count,
        "is_visible": sketch.isVisible
    }

@command()
def get_body_properties(app, body_name):
    body = _get_body(app, body_name)
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

@command()
def get_object_hierarchy(app):
    """Returns the full design object hierarchy showing name and type of every object.

    Recursively traverses the component tree starting from the root component,
    collecting bodies, sketches, joints, construction planes/axes/points, and
    features for each component.  Sub-components are listed as children via
    their occurrences.
    """
    design = get_active_design(app)
    root = design.rootComponent

    def _collect_component(comp, occurrence_name=None):
        """Build a dict describing one component and its contents."""
        node = {
            "name": comp.name,
            "type": "Component",
        }
        if occurrence_name:
            node["occurrence"] = occurrence_name

        # Bodies
        bodies = []
        for i in range(comp.bRepBodies.count):
            b = comp.bRepBodies.item(i)
            bodies.append({"name": b.name, "type": "BRepBody", "is_visible": b.isVisible})
        if bodies:
            node["bodies"] = bodies

        # Sketches
        sketches = []
        for i in range(comp.sketches.count):
            s = comp.sketches.item(i)
            sketches.append({
                "name": s.name,
                "type": "Sketch",
                "profiles_count": s.profiles.count,
                "is_visible": s.isVisible,
            })
        if sketches:
            node["sketches"] = sketches

        # Features (timeline-based operations)
        features = []
        try:
            for i in range(comp.features.count):
                f = comp.features.item(i)
                feat_type = f.objectType.split("::")[-1] if hasattr(f, "objectType") else "Feature"
                feat = {"name": f.name, "type": feat_type}
                try:
                    feat["is_suppressed"] = f.isSuppressed
                except:
                    pass
                features.append(feat)
        except:
            pass
        if features:
            node["features"] = features

        # Joints (only on root component)
        joints = []
        try:
            for i in range(comp.joints.count):
                j = comp.joints.item(i)
                jt = j.objectType.split("::")[-1] if hasattr(j, "objectType") else "Joint"
                joints.append({"name": j.name, "type": jt})
        except:
            pass
        try:
            for i in range(comp.asBuiltJoints.count):
                j = comp.asBuiltJoints.item(i)
                jt = j.objectType.split("::")[-1] if hasattr(j, "objectType") else "AsBuiltJoint"
                joints.append({"name": j.name, "type": jt})
        except:
            pass
        if joints:
            node["joints"] = joints

        # Construction geometry
        construction = []
        try:
            for i in range(comp.constructionPlanes.count):
                cp = comp.constructionPlanes.item(i)
                construction.append({"name": cp.name, "type": "ConstructionPlane"})
        except:
            pass
        try:
            for i in range(comp.constructionAxes.count):
                ca = comp.constructionAxes.item(i)
                construction.append({"name": ca.name, "type": "ConstructionAxis"})
        except:
            pass
        try:
            for i in range(comp.constructionPoints.count):
                cp = comp.constructionPoints.item(i)
                construction.append({"name": cp.name, "type": "ConstructionPoint"})
        except:
            pass
        if construction:
            node["construction_geometry"] = construction

        # Child components (via occurrences)
        children = []
        for i in range(comp.occurrences.count):
            occ = comp.occurrences.item(i)
            child = _collect_component(occ.component, occurrence_name=occ.name)
            child["is_visible"] = occ.isVisible
            children.append(child)
        if children:
            node["children"] = children

        return node

    hierarchy = _collect_component(root)
    hierarchy["design_name"] = design.rootComponent.name
    hierarchy["design_type"] = "DirectDesignType" if design.designType == 0 else "ParametricDesignType"

    return {"hierarchy": hierarchy}
