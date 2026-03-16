# Fusion 360 MCP Cheat Sheet for LLMs

This document provides the "Mental Model" and essential constraints for interacting with the Fusion 360 MCP server effectively.

## 📐 Core Conventions & Units

- **Length Units**: All raw numbers are in **Centimeters (cm)**. If you need 50mm, send `5.0`.
- **Angle Units**: Most tools expect **Degrees**, unless specified as Radians (rare).
- **Coordinate System**: 
  - **Z-Up** or **Y-Up**: Default Fusion 360 is typically Y-Up (legacy) or Z-Up (modern). **Check the orientation before complex modeling.**
  - **Origin**: (0,0,0) is the center of the universe.
- **Timeline**: Fusion 360 is a **parametric, history-based** CAD. Every feature (extrude, fillet, etc.) is an entry in the timeline.

## 🛠️ Essential Workflow Patterns

### 1. The Sketch-Feature Loop
Most 3D geometry starts with a sketch:
1. `create_sketch(plane_name="XY")` -> Returns "Sketch1".
2. `add_line("Sketch1", ...)` or `add_circle(...)` to draw.
3. `get_sketch_info("Sketch1")` to verify profiles were created.
4. `create_extrude(sketch_name="Sketch1", distance=2.0)` -> Creates a 3D body.

### 2. Modeling on Faces
To build "outward" from an existing part:
1. `find_faces(body_name="Body1")` -> Look for a face with the correct normal (e.g., `{0,0,1}` for Top).
2. `create_sketch(body_name="Body1", face_index=3)` using the index from step 1.
3. Draw on the new sketch (coordinates are relative to the face origin).

### 3. Precision & Constraints
Avoid "naked" geometry. Use constraints to make models robust:
- Use `apply_constraint` (e.g., "horizontal", "vertical", "equal").
- Use `add_distance_dimension` to lock in sizes.
- Use `create_user_parameter` for reusable values (e.g., `wall_thickness = 0.3`).

### 4. Assemblies
- Create components (`create_component`) to logically separate parts.
- Use `create_joint` or `create_as_built_joint` to connect them. Supported types: `rigid`, `revolute`, `slider`, `cylindrical`, `pin_slot`, `planar`, `ball`.

### 5. Reverse Engineering / Mesh Workflow
To reconstruct or modify a parametric solid base from an existing STL/OBJ:
1. `import_mesh(file_path)` to bring the mesh into the design.
2. `convert_mesh_to_solid(body_name="Mesh Body 1", method="prismatic")` to natively convert the mesh triangles into an editable BRep/Solid BaseFeature. (Note: Prismatic is preferred for mechanical parts).
3. Use downstream solid tools like `create_extrude`, `split_body`, or `create_hole` to adjust the now-solid geometry.

### 6. Design Management
Keep your work organized and accessible:
- Use `list_projects` to find where designs are stored.
- Use `create_folder` to organize by part or assembly.
- Use `list_designs(project_name)` to see what's available.
- Use `open_design(project_name, design_name)` to load an existing file.
- Use `save_design()` (from utils) to commit your changes with a description.
- Use `create_new_design(name, project_name)` to start fresh in a specific location.

### 7. Updating the MCP Server & Add-in

## ⚠️ Common Pitfalls

- **Closed Profiles**: Features like `create_extrude` require a **closed loop** of lines/arcs. If your sketch isn't "water-tight", it will fail or extrude unexpected regions.
- **Naming**: Always name your bodies and sketches (`rename_body`, `rename_sketch`) to keep track of them in complex designs.
- **Timeline Health**: If a command returns `new_issues`, it means you broke a previous feature or constraint. Check `get_design_health()`.
- **Auto-Grouping**: The add-in automatically groups operations into "Group: [method]". Use `start_timeline_group` for intentional manual grouping.

## 🔍 Inspection Tools
- `get_body_properties`: Mass, Volume, Bounding Box.
- `find_faces` / `get_edge_info`: Essential for identifying indices for downstream features (fillets, chamfers, new sketches).
- `list_parameters`: Check existing variables.
