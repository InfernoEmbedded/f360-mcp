import adsk.core
import adsk.fusion
from . import command
from .base import get_active_design, _get_body

@command()
def list_materials(app):
    design = get_active_design(app)
    materials = []
    for i in range(design.materials.count):
        m = design.materials.item(i)
        materials.append({"name": m.name, "library": "Design"})
    lib = app.materialLibraries.itemByName("Fusion 360 Material Library")
    if lib:
        for i in range(lib.materials.count):
            m = lib.materials.item(i)
            materials.append({"name": m.name, "library": lib.name})
            if len(materials) > 100:
                break
    return {"materials": materials}

@command()
def apply_material(app, body_name, material_name):
    design = get_active_design(app)
    body = _get_body(app, body_name)
    material = design.materials.itemByName(material_name)
    if not material:
        lib = app.materialLibraries.itemByName("Fusion 360 Material Library")
        if lib:
            material = lib.materials.itemByName(material_name)
    if not material:
        raise Exception(f"Material '{material_name}' not found.")
    body.material = material
    return {"message": f"Successfully applied material '{material_name}' to body '{body_name}'."}

@command()
def list_appearances(app):
    design = get_active_design(app)
    appearances = []
    for i in range(design.appearances.count):
        a = design.appearances.item(i)
        appearances.append({"name": a.name, "library": "Design"})
    lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
    if lib:
        for i in range(lib.appearances.count):
            a = lib.appearances.item(i)
            appearances.append({"name": a.name, "library": lib.name})
            if len(appearances) > 100:
                break
    return {"appearances": appearances}

@command()
def apply_appearance(app, body_name, appearance_name):
    design = get_active_design(app)
    body = _get_body(app, body_name)
    appearance = design.appearances.itemByName(appearance_name)
    if not appearance:
        lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
        if lib:
            appearance = lib.appearances.itemByName(appearance_name)
    if not appearance:
        raise Exception(f"Appearance '{appearance_name}' not found.")
    body.appearance = appearance
    return {"message": f"Successfully applied appearance '{appearance_name}' to body '{body_name}'."}
