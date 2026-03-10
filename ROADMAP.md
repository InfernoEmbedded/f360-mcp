# Fusion 360 MCP Wrapper Sketch API Roadmap

This document outlines the current implementation status of the Fusion 360 Sketch API exposed via Model Context Protocol (MCP).

## Implemented Features
The following tools have been implemented and are ready for use:

- [x] **`create_sketch`**: Create a new sketch on a specified base plane (XY, XZ, YZ).
- [x] **`add_circle`**: Add a circle by center point and radius to a sketch.
- [x] **`add_line`**: Add a line segment by start and end points to a sketch.

## Unimplemented Features (TODO)
There are many geometries and sketch operations in the Fusion 360 API that are not yet exposed:

### Geometries
- [ ] Add Rectangle (Center, 2-Point, 3-Point)
- [ ] Add Arc (Center Point, 3-Point, Tangent)
- [ ] Add Spline (Fit Point, Control Point)
- [ ] Add Polygon (Circumscribed, Inscribed, Edge)
- [ ] Add Ellipse
- [ ] Add Point
- [ ] Add Text

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

### Utilities
- [ ] Project Geometry
- [ ] Offset Geometry
- [ ] Trim/Extend Geometry
- [ ] Mirror Geometry
- [ ] List available sketches in active design
- [ ] Delete sketch
