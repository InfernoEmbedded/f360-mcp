import adsk.core
import adsk.fusion
from . import command
from .base import get_active_design, find_occ

@command()
def create_component(app, name):
    design = get_active_design(app)
    rootComp = design.rootComponent
    occurrences = rootComp.occurrences
    transform = adsk.core.Matrix3D.create()
    occ = occurrences.addNewComponent(transform)
    comp = occ.component
    comp.name = name
    return {"message": f"Created component '{name}'. Note: modeling still default happens in root component via MCP.", "component_name": comp.name}

@command()
def list_components(app):
    design = get_active_design(app)
    rootComp = design.rootComponent
    comp_list = []
    for i in range(rootComp.occurrences.count):
        occ = rootComp.occurrences.item(i)
        comp = occ.component
        comp_list.append({
            "name": comp.name,
            "occurrence_name": occ.name,
            "is_visible": occ.isVisible
        })
    return {"components": comp_list}

@command()
def rename_component(app, old_name, new_name):
    design = get_active_design(app)
    for comp in design.allComponents:
        if comp.name == old_name:
            comp.name = new_name
            return {"message": f"Renamed component '{old_name}' to '{new_name}'"}
    raise Exception(f"Component '{old_name}' not found.")

@command()
def delete_component(app, occurrence_name):
    design = get_active_design(app)
    rootComp = design.rootComponent
    occ = rootComp.occurrences.itemByName(occurrence_name)
    if not occ:
        raise Exception(f"Component occurrence '{occurrence_name}' not found in root.")
    occ.deleteMe()
    return {"message": f"Deleted component instance '{occurrence_name}'"}

@command()
def create_joint(app, component1_name, component2_name, joint_type="rigid", offset_x=0, offset_y=0, offset_z=0):
    design = get_active_design(app)
    root = design.rootComponent
    occ1 = find_occ(app, component1_name)
    occ2 = find_occ(app, component2_name)
    joints = root.joints
    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1.component.originConstructionPoint)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2.component.originConstructionPoint)
    jointInput = joints.createInput(geo0, geo1)
    jt = joint_type.lower()
    if jt == "rigid":
        jointInput.setAsRigidJointMotion()
    elif jt == "revolute":
        jointInput.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "slider":
        jointInput.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    if offset_x != 0 or offset_y != 0 or offset_z != 0:
        offset = adsk.core.Vector3D.create(offset_x, offset_y, offset_z)
        jointInput.offset = offset
    joint = joints.add(jointInput)
    return {"message": f"Created {joint_type} joint.", "joint_name": joint.name}

@command()
def create_as_built_joint(app, component1_name, component2_name, joint_type="rigid"):
    design = get_active_design(app)
    root = design.rootComponent
    occ1 = find_occ(app, component1_name)
    occ2 = find_occ(app, component2_name)
    joints = root.asBuiltJoints
    jointInput = joints.createInput(occ1, occ2, None)
    jt = joint_type.lower()
    if jt == "rigid":
        jointInput.setAsRigidJointMotion()
    elif jt == "revolute":
        jointInput.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    joint = joints.add(jointInput)
    return {"message": f"Created as-built {joint_type} joint.", "joint_name": joint.name}
