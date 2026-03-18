import adsk.core
import adsk.fusion
import logging

logger = logging.getLogger('f360_mcp')

_group_stack = []

def get_active_design(app):
    if not app:
        return None
    try:
        design = app.activeProduct
        if not design or not design.isValid or not hasattr(design, 'rootComponent'): # Check if it's a design and valid
            return None
        return design
    except:
        return None

def _get_body(app, name):
    design = get_active_design(app)
    # Check root first
    rootComp = design.rootComponent
    for i in range(rootComp.bRepBodies.count):
        b = rootComp.bRepBodies.item(i)
        if b.name == name:
            logger.debug(f"Found body '{name}' in rootComponent.")
            return b
    # Check all components
    for comp in design.allComponents:
        for i in range(comp.bRepBodies.count):
            b = comp.bRepBodies.item(i)
            if b.name == name:
                logger.debug(f"Found body '{name}' in component '{comp.name}'.")
                return b
    
    # Log all existing bodies if not found
    all_bodies = [b.name for b in rootComp.bRepBodies]
    for comp in design.allComponents:
        all_bodies.extend([b.name for b in comp.bRepBodies])
    logger.error(f"Body '{name}' not found. Available bodies: {all_bodies}")
    raise Exception(f"Body '{name}' not found.")
    
def _get_feature(app, name):
    design = get_active_design(app)
    rootComp = design.rootComponent
    # Search all features in root
    for i in range(rootComp.features.count):
        feat = rootComp.features.item(i)
        if feat.name == name:
            return feat
    # Search in all components
    for comp in design.allComponents:
        for i in range(comp.features.count):
            feat = comp.features.item(i)
            if feat.name == name:
                logger.debug(f"Found feature '{name}' in component '{comp.name}'.")
                return feat
    
    # Log all existing features if not found
    all_feats = [f.name for f in rootComp.features]
    for comp in design.allComponents:
        all_feats.extend([f.name for f in comp.features])
    logger.error(f"Feature '{name}' not found. Available features: {all_feats}")
    raise Exception(f"Feature '{name}' not found.")

def get_sketch_by_name(app, sketch_name):
    design = get_active_design(app)
    # Search all components for the sketch
    for comp in design.allComponents:
        sketch = comp.sketches.itemByName(sketch_name)
        if sketch:
            return sketch
    raise Exception(f"Sketch named {sketch_name} not found.")

def find_occ(app, name):
    design = get_active_design(app)
    root = design.rootComponent
    for occ in root.allOccurrences:
        if occ.name == name or occ.component.name == name:
            return occ
    raise Exception(f"Occurrence '{name}' not found.")

def _start_group(app):
    design = get_active_design(app)
    group = design.timeline.timelineGroups.add(design.timeline.count, design.timeline.count)
    _group_stack.append(group)
    return group

def _stop_group():
    if _group_stack:
        return _group_stack.pop()
    return None

def _is_internal_command(name):
    return name in ['start_timeline_group', 'stop_timeline_group']

def _get_timeline_health_map(app):
    """
    Internal helper to get a map of timeline item health.
    Used for detecting new issues after an operation.
    """
    try:
        design = get_active_design(app)
        if not design:
            return {}
        timeline = design.timeline
        if not timeline or not timeline.isValid:
            return {}
        
        health_map = {}
        for i in range(timeline.count):
            try:
                item = timeline.item(i)
                if not item or not item.isValid:
                    continue
                state = item.healthState
                if state != 0 and state != 3: # Not Success and not Info
                    msg = ""
                    try:
                        msg = item.errorOrWarningMessage
                    except:
                        pass
                    # Use a stable-ish key: index + type
                    health_map[i] = (item.objectType, state, msg)
            except:
                continue
        return health_map
    except:
        return {}
