import adsk.core
import adsk.fusion
import traceback
from . import command
from .base import get_active_design, _start_group, _stop_group

@command()
def undo(app, steps=1):
    """
    Performs global undo steps in the active document.

    Args:
        steps (int): Number of steps to undo. Default: 1.

    Examples:
        call_addin("undo", {"steps": 1})
    """
    design = get_active_design(app)
    for _ in range(steps):
        app.activeDocument.undo()
    return {"message": f"Global undo performed {steps} times."}

@command()
def redo(app, steps=1):
    """
    Performs global redo steps in the active document.

    Args:
        steps (int): Number of steps to redo. Default: 1.

    Examples:
        call_addin("redo", {"steps": 1})
    """
    design = get_active_design(app)
    for _ in range(steps):
        app.activeDocument.redo()
    return {"message": f"Global redo performed {steps} times."}

@command()
def save_design(app, description="Saved via MCP"):
    """
    Saves the currently active Fusion document.
    
    Note: Requires the document to already have a file location (not new).

    Args:
        description (str): Version description for the save event.

    Examples:
        call_addin("save_design", {"description": "Milestone check-in"})
    """
    design = get_active_design(app)
    if design.isNew:
        raise Exception("Document is new. Use 'create_new_design' with save parameters or save manually first.")
    design.save(description)
    return {"message": "Design saved successfully."}

@command()
def capture_screenshot(app, file_path, width=1280, height=720, send_to_mcp=False):
    """
    Captures an image of the active viewport.

    Args:
        file_path (str): Local path to save the image.
        width (int): Pixel width. Default: 1280.
        height (int): Pixel height. Default: 720.
        send_to_mcp (bool): If True, returns the image data as base64.

    Examples:
        call_addin("capture_screenshot", {"file_path": "C:/Temp/View.png", "send_to_mcp": True})
    """
    import base64
    import os
    app.activeViewport.refresh()
    success = app.activeViewport.saveAsImageFile(file_path, width, height)
    if not success:
        raise Exception("Failed to save screenshot.")
    result = {"message": f"Screenshot saved to {file_path}", "file_path": file_path}
    if send_to_mcp:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                result["file_content_base64"] = encoded
    return result

@command()
def execute_script(app, script_code):
    """
    Executes raw Python code within the Fusion 360 environment.
    
    HAZARDOUS: Provides full access to the Fusion 360 API. Use with caution.

    Args:
        script_code (str): The Python code string to execute.

    Returns:
        dict: {"message": str, "result": obj}

    Examples:
        call_addin("execute_script", {"script_code": "result = app.name"})
    """
    import adsk.core
    ui = app.userInterface
    exec_globals = {
        'app': app,
        'ui': ui,
        'adsk': adsk,
        'result': None
    }
    try:
        exec(script_code, exec_globals)
        return {"message": "Script executed successfully.", "result": exec_globals.get('result')}
    except Exception as e:
        error_info = traceback.format_exc()
        raise Exception(f"Script Error: {str(e)}\n\nTraceback:\n{error_info}")

@command()
def start_timeline_group(app, name):
    """
    Starts a new group in the design timeline.
    
    Grouping subsequent features keeps the timeline organized.

    Args:
        name (str): Name for the group.

    Examples:
        call_addin("start_timeline_group", {"name": "WheelAssembly"})
    """
    _start_group(app)
    return {"message": f"Started timeline group: {name}"}

@command()
def stop_timeline_group(app):
    """
    Closes the currently active timeline group.

    Examples:
        call_addin("stop_timeline_group", {})
    """
    _stop_group()
    return {"message": "Stopped timeline group."}

@command()
def rename_sketch(app, old_name, new_name):
    """
    Renames a sketch.

    Args:
        old_name (str): Current name.
        new_name (str): New name.

    Examples:
        call_addin("rename_sketch", {"old_name": "Sketch1", "new_name": "MainProfile"})
    """
    from .base import get_sketch_by_name
    sketch = get_sketch_by_name(app, old_name)
    sketch.name = new_name
    return {"message": f"Renamed sketch '{old_name}' to '{new_name}'", "new_name": sketch.name}
