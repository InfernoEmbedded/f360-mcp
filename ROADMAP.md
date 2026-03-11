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
- [x] **`delete_sketch`**: Delete an entire sketch by name.
- [x] **`project_geometry`**: Project geometry from another sketch.
- [x] **`offset_geometry`**: Create an offset of a sketch entity.
- [x] **`trim_sketch_geometry`**: Trim a sketch curve using a coordinate point.
- [x] **`delete_sketch_entity`**: Delete a specific entity inside a sketch.

### Solid Modeling Phase 1 (Essentials)
- [x] **`create_extrude`**: Extrude a sketch profile.
- [x] **`create_revolve`**: Revolve a sketch profile around an axis.
- [x] **`create_sweep`**: Sweep a profile along a path.
- [x] **`create_loft`**: Create a loft across multiple profiles.

### Solid Modeling Phase 2 (Modification)
- [x] **`combine_bodies`**: Join, cut, or intersect bodies.
- [x] **`list_bodies`**: List all bodies in the active design.
- [x] **`create_hole`**: Create a hole from a point.
- [x] **`create_shell`**: Shell a body to a specific thickness.

## Unimplemented Features (TODO)

### Solid Modeling Phase 3 (Finishing)
- [x] **`create_fillet`**: Add a fillet to an edge or face.
- [x] **`create_chamfer`**: Add a chamfer to an edge or face.
- [x] **`feature_mirror`**: Mirror a body or feature.

## Unimplemented Features (TODO)

### Utilities & Operations (Deferred due to API limits)
- [ ] Extend Geometry
- [ ] Mirror Geometry
- [ ] Delete sketch
