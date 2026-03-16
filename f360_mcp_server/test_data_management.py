import pytest
from f360_mcp_server.server import list_projects, create_project, create_folder, create_new_design

@pytest.mark.anyio
async def test_project_management(mock_fusion):
    # 1. List projects
    res_list = await list_projects()
    projects = res_list["projects"]
    assert len(projects) >= 2
    assert any(p["name"] == "Test Project" for p in projects)
    
    # 2. Create project
    res_create = await create_project(name="New MCP Project")
    assert "Created project 'New MCP Project'" in res_create["message"]
    assert res_create["project_id"] == "new_proj_id"

@pytest.mark.anyio
async def test_data_management(mock_fusion, recorded_commands):
    await list_projects()
    await create_project(name="Project1")
    await create_folder(project_name="Project1", folder_name="Folder1")
    from test_utils import compare_command_logs
    compare_command_logs("test_data_management", recorded_commands)

@pytest.mark.anyio
async def test_folder_management(mock_fusion):
    # 1. Create folder
    res_folder = await create_folder(
        project_name="Test Project", 
        folder_name="Components"
    )
    assert "Created folder 'Components'" in res_folder["message"]
    assert res_folder["folder_id"] == "new_folder_id"
    
    # 2. Create subfolder
    res_subfolder = await create_folder(
        project_name="Test Project", 
        folder_name="SubDir", 
        parent_folder_path="Components"
    )
    assert "Created folder 'SubDir'" in res_subfolder["message"]

@pytest.mark.anyio
async def test_design_creation(mock_fusion):
    # 1. Create unsaved design
    res_unsaved = await create_new_design(name="Draft1")
    assert "Created new unsaved design 'Draft1'" in res_unsaved["message"]
    assert res_unsaved["status"] == "unsaved"
    
    # 2. Create and save design
    res_saved = await create_new_design(
        name="EngineV1", 
        project_name="Test Project", 
        folder_path="Components"
    )
    assert "Created and saved design 'EngineV1'" in res_saved["message"]
    assert res_saved["status"] == "saved"
