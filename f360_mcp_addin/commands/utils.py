import adsk.core
import adsk.fusion
import traceback
from . import command
from .base import get_active_design, _start_group, _stop_group

@command()
def undo(app, steps=1):
    design = get_active_design(app)
    for _ in range(steps):
        app.activeDocument.undo()
    return {"message": f"Global undo performed {steps} times."}

@command()
def redo(app, steps=1):
    design = get_active_design(app)
    for _ in range(steps):
        app.activeDocument.redo()
    return {"message": f"Global redo performed {steps} times."}

@command()
def save_design(app, description="Saved via MCP"):
    design = get_active_design(app)
    if design.isNew:
        raise Exception("Document is new. Use 'create_new_design' with save parameters or save manually first.")
    design.save(description)
    return {"message": "Design saved successfully."}

@command()
def capture_screenshot(app, file_path, width=1280, height=720, send_to_mcp=False):
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
    _start_group(app)
    return {"message": f"Started timeline group: {name}"}

@command()
def stop_timeline_group(app):
    _stop_group()
    return {"message": "Stopped timeline group."}

@command()
def rename_sketch(app, old_name, new_name):
    from .base import get_sketch_by_name
    sketch = get_sketch_by_name(app, old_name)
    sketch.name = new_name
    return {"message": f"Renamed sketch '{old_name}' to '{new_name}'", "new_name": sketch.name}
