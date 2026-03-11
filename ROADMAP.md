# Fusion 360 MCP Wrapper Sketch API Roadmap

This document outlines the current implementation status of the Fusion 360 Sketch API exposed via Model Context Protocol (MCP).

# Fusion 360 MCP Wrapper Sketch API Roadmap

This document outlines the current status of the Fusion 360 Sketch API exposed via Model Context Protocol (MCP).

## Implemented Features

### Setup & Management
- [x] **`create_sketch`**: Create a new sketch on a specified base plane (XY, XZ, YZ).

### Geometries
- [x] **`add_line`**: Add a line segment by start and end points.
- [x] **`add_circle`**: Add a circle by center point and radius.
- [x] **`add_rectangle`**: Add 2-point, 3-point, or center-point rectangles.
- [x] **`add_arc`**: Add 3-point or center-start-sweep arcs.
- [x] **`add_spline`**: Add a fitted spline through a list of points.
- [x] **`add_polygon`**: Add circumscribed or inscribed regular polygons.
- [x] **`add_ellipse`**: Add an ellipse via center and major/minor points.
- [x] **`add_point`**: Add individual sketch points.
- [x] **`add_text`**: Add text to a sketch with custom height.

### Constraints
- [x] **`apply_constraint`**: Add Coincident, Collinear, Concentric, MidPoint, Parallel, Perpendicular, Horizontal, Vertical, Tangent, and Equal constraints.
- [x] **`add_symmetry_constraint`**: Add a symmetry constraint between two entities and a symmetry line.

### Dimensions
- [x] **`add_distance_dimension`**: Add aligned, horizontal, or vertical dimension.
- [x] **`add_radial_dimension`**: Add radial dimension to an arc or circle.
- [x] **`add_diameter_dimension`**: Add diameter dimension to a circle or arc.
- [x] **`add_angular_dimension`**: Add angular dimension between two lines.

### Utilities & Operations
- [x] **`list_sketches`**: List all sketches in the design.
- [x] **`delete_sketch`**: Delete a sketch by name.
- [x] **`project_geometry`**: Project geometry from another sketch.
- [x] **`offset_geometry`**: Create an offset of a sketch entity.

## Unimplemented Features (TODO)

### Utilities & Operations (Deferred due to API limits)
- [ ] Trim Geometry
- [ ] Extend Geometry
- [ ] Mirror Geometry
es in active design
- [ ] Delete sketch
