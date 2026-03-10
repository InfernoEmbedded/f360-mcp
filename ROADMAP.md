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

## Unimplemented Features (TODO)

### Constraints
- [ ] Add Coincident Constraint
- [ ] Add Collinear Constraint
- [ ] Add Concentric Constraint
- [ ] Add MidPoint Constraint
- [ ] Add Parallel Constraint
- [ ] Add Perpendicular Constraint
- [ ] Add Horizontal/Vertical Constraint
- [ ] Add Tangent Constraint
- [ ] Add Equal Constraint
- [ ] Add Symmetry Constraint

### Dimensions
- [ ] Add Linear Dimension
- [ ] Add Radial/Diameter Dimension
- [ ] Add Angular Dimension

### Utilities & Operations
- [ ] Project Geometry
- [ ] Offset Geometry
- [ ] Trim/Extend Geometry
- [ ] Mirror Geometry
- [ ] List available sketches in active design
- [ ] Delete sketch
