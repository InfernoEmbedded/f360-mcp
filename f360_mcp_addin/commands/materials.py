import adsk.core
import adsk.fusion
from . import command
from .base import get_active_design, _get_body

@command()
def list_materials(app, include_downloadable=True):
    """
    Lists physical materials available in the design or library.

    Args:
        include_downloadable (bool): If True, includes materials not yet downloaded.

    Returns:
        dict: {"materials": [{"name": str, "library": str, "is_downloaded": bool}, ...]}

    Examples:
        call_addin("list_materials", {"include_downloadable": False})
    """
    design = get_active_design(app)
    materials = []
    
    # Materials already in the design
    for i in range(design.materials.count):
        m = design.materials.item(i)
        materials.append({
            "name": m.name, 
            "library": "Design",
            "is_downloaded": True
        })
        
    lib = app.materialLibraries.itemByName("Fusion 360 Material Library")
    if lib:
        for i in range(lib.materials.count):
            m = lib.materials.item(i)
            # Filter if required
            is_downloaded = getattr(m, 'isDownloaded', True)
            if not include_downloadable and not is_downloaded:
                continue
                
            materials.append({
                "name": m.name, 
                "library": lib.name,
                "is_downloaded": is_downloaded
            })
            if len(materials) > 400: # Increased limit
                break
    return {"materials": materials}

@command()
def apply_material(app, body_name, material_name):
    """
    Assigns a physical material to a solid body.

    Args:
        body_name (str): Target body.
        material_name (str): Material name (e.g., "Steel", "Aluminum").

    Examples:
        call_addin("apply_material", {"body_name": "BracketBody", "material_name": "Steel"})
    """
    design = get_active_design(app)
    body = _get_body(app, body_name)
    
    material = design.materials.itemByName(material_name)
    if not material:
        lib = app.materialLibraries.itemByName("Fusion 360 Material Library")
        if lib:
            material = lib.materials.itemByName(material_name)
            
    if not material:
        raise Exception(f"Material '{material_name}' not found.")
        
    # Download if needed
    if hasattr(material, 'isDownloaded') and not material.isDownloaded:
        try:
            material.download()
        except Exception as e:
            raise Exception(f"Failed to download material '{material_name}': {e}")
            
    body.material = material
    return {"message": f"Successfully applied material '{material_name}' to body '{body_name}'."}

@command()
def list_appearances(app, include_downloadable=True):
    """
    Lists appearances (visual styles) available in the design or library.

    Args:
        include_downloadable (bool): If True, includes appearances not yet downloaded.

    Returns:
        dict: {"appearances": [{"name": str, "library": str, "has_texture": bool, ...}, ...]}

    Examples:
        call_addin("list_appearances", {})
    """
    design = get_active_design(app)
    appearances = []
    
    # Appearances already in the design
    for i in range(design.appearances.count):
        a = design.appearances.item(i)
        appearances.append({
            "name": a.name, 
            "library": "Design",
            "is_downloaded": True,
            "has_texture": getattr(a, 'hasTexture', False)
        })
        
    # Appearances from the main library
    lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
    if lib:
        for i in range(lib.appearances.count):
            a = lib.appearances.item(i)
            # Filter if required
            is_downloaded = getattr(a, 'isDownloaded', True)
            if not include_downloadable and not is_downloaded:
                continue
                
            appearances.append({
                "name": a.name, 
                "library": lib.name,
                "is_downloaded": is_downloaded,
                "has_texture": getattr(a, 'hasTexture', False)
            })
            if len(appearances) > 400: # Increased limit to see more
                break
    return {"appearances": appearances}

@command()
def apply_appearance(app, body_name, appearance_name):
    """
    Assigns a visual appearance to a solid body.

    Args:
        body_name (str): Target body.
        appearance_name (str): Appearance name (e.g., "Paint - Glossy (Black)").

    Examples:
        call_addin("apply_appearance", {"body_name": "BracketBody", "appearance_name": "Chrome"})
    """
    design = get_active_design(app)
    body = _get_body(app, body_name)
    
    appearance = design.appearances.itemByName(appearance_name)
    if not appearance:
        lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
        if lib:
            appearance = lib.appearances.itemByName(appearance_name)
            
    if not appearance:
        raise Exception(f"Appearance '{appearance_name}' not found.")
        
    # Download if needed
    if hasattr(appearance, 'isDownloaded') and not appearance.isDownloaded:
        # download() method exists on Appearance objects in Fusion
        # Note: If it's a synchronous call it blocks, but we are inside the main thread execution block
        try:
            appearance.download()
        except Exception as e:
            raise Exception(f"Failed to download appearance '{appearance_name}': {e}")
            
    body.appearance = appearance
    return {"message": f"Successfully applied appearance '{appearance_name}' to body '{body_name}'."}
