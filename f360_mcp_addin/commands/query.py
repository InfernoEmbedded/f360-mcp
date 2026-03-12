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
