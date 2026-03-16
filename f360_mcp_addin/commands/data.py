import adsk.core
import adsk.fusion
import base64
import os
from . import command
from .base import get_active_design, _get_body

def _get_folder_by_path(project, folder_path):
    """Helper to navigate a project's folder structure."""
    current_folder = project.rootFolder
    if folder_path:
        parts = [p for p in folder_path.split('/') if p]
        for part in parts:
            found = False
            for i in range(current_folder.dataFolders.count):
                if current_folder.dataFolders.item(i).name == part:
                    current_folder = current_folder.dataFolders.item(i)
                    found = True
                    break
            if not found:
                raise Exception(f"Folder path component '{part}' not found.")
    return current_folder

@command()
def list_projects(app):
    hubs = app.data.hubs
    projects_list = []
    for h_idx in range(hubs.count):
        hub = hubs.item(h_idx)
        projects = hub.dataProjects
        for p_idx in range(projects.count):
            proj = projects.item(p_idx)
            projects_list.append({
                "name": proj.name,
                "id": proj.id,
                "hub": hub.name
            })
    return {"projects": projects_list}

@command()
def create_project(app, name):
    hub = app.data.activeHub
    projects = hub.dataProjects
    for i in range(projects.count):
        if projects.item(i).name == name:
            return {"message": f"Project '{name}' already exists.", "project_id": projects.item(i).id}
    project = projects.add(name)
    return {"message": f"Project '{name}' created successfully.", "project_id": project.id}

@command()
def create_folder(app, project_name, folder_name, parent_folder_path=None):
    hub = app.data.activeHub
    project = None
    for i in range(hub.dataProjects.count):
        if hub.dataProjects.item(i).name == project_name:
            project = hub.dataProjects.item(i)
            break
    if not project:
        raise Exception(f"Project '{project_name}' not found.")
    
    current_folder = _get_folder_by_path(project, parent_folder_path)
    
    for i in range(current_folder.dataFolders.count):
        if current_folder.dataFolders.item(i).name == folder_name:
            return {"message": f"Folder '{folder_name}' already exists.", "folder_id": current_folder.dataFolders.item(i).id}
            
    folder = current_folder.dataFolders.add(folder_name)
    return {"message": f"Folder '{folder_name}' created successfully.", "folder_id": folder.id}

@command()
def list_designs(app, project_name, folder_path=None):
    """
    Lists designs in a project and folder.
    
    Args:
        project_name: Name of the project.
        folder_path: Optional path to a subfolder (e.g. "Mechanical/Parts").
    """
    hub = app.data.activeHub
    project = None
    for i in range(hub.dataProjects.count):
        if hub.dataProjects.item(i).name == project_name:
            project = hub.dataProjects.item(i)
            break
    if not project:
        raise Exception(f"Project '{project_name}' not found.")
    
    folder = _get_folder_by_path(project, folder_path)
    
    data_files = []
    for i in range(folder.dataFiles.count):
        df = folder.dataFiles.item(i)
        # Check if it's a Fusion design (FusionDesignDocumentType doesn't apply to DataFile)
        # We'll just return everything in the folder, usually they are designs.
        data_files.append({
            "name": df.name,
            "id": df.id,
            "version": df.versionNumber
        })
        
    return {"designs": data_files}

@command()
def open_design(app, project_name, name, folder_path=None):
    """
    Opens an existing design.
    
    Args:
        project_name: Name of the project.
        name: Name of the design file.
        folder_path: Optional path to a subfolder.
    """
    hub = app.data.activeHub
    project = None
    for i in range(hub.dataProjects.count):
        if hub.dataProjects.item(i).name == project_name:
            project = hub.dataProjects.item(i)
            break
    if not project:
        raise Exception(f"Project '{project_name}' not found.")
    
    folder = _get_folder_by_path(project, folder_path)
    
    data_file = None
    for i in range(folder.dataFiles.count):
        df = folder.dataFiles.item(i)
        if df.name == name:
            data_file = df
            break
            
    if not data_file:
        raise Exception(f"Design '{name}' not found in '{project_name}' (folder: {folder_path or 'root'})")
        
    doc = app.documents.open(data_file, True)
    if not doc:
        raise Exception(f"Failed to open design '{name}'")
        
    return {"message": f"Successfully opened design '{name}'", "document_name": doc.name}

@command()
def create_new_design(app, name, project_name=None, folder_path=None):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.itemByName('Untitled').parent.name = name # This is tricky, usually you just save it
    
    if project_name:
        hub = app.data.activeHub
        project = None
        for i in range(hub.dataProjects.count):
            if hub.dataProjects.item(i).name == project_name:
                project = hub.dataProjects.item(i)
                break
        if not project:
            return {"message": f"Design created but could not find project '{project_name}' to save.", "status": "unsaved"}
            
        current_folder = _get_folder_by_path(project, folder_path)
        
        doc.saveAs(name, current_folder, "", "")
        return {"message": f"Created and saved design '{name}' in project '{project_name}'", "status": "saved"}
        
    return {"message": f"Created design '{name}' (unsaved).", "status": "unsaved"}

@command()
def export_model(app, file_path, file_type="step", body_name=None, send_to_mcp=False):
    design = get_active_design(app)
    exportMgr = design.exportManager
    rootComp = design.rootComponent
    target = rootComp
    if body_name:
        target = _get_body(app, body_name)
    
    if file_type.lower() == "step":
        if body_name:
            raise Exception("STEP export currently only supported for the full component in this wrapper.")
        options = exportMgr.createSTEPExportOptions(file_path)
    elif file_type.lower() == "stl":
        options = exportMgr.createSTLExportOptions(target, file_path)
    elif file_type.lower() == "3mf":
        try:
            options = exportMgr.create3MFExportOptions(target, file_path)
        except AttributeError:
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
