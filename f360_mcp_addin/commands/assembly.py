import adsk.core
import adsk.fusion
import math
from . import command
from .base import get_active_design, find_occ

@command()
def create_component(app, name):
    """
    Creates a new empty component (occurrence) in the root assembly.
    
    Components allow for modular design and and are required for joints.

    Args:
        name (str): Unique name for the new component.

    Examples:
        call_addin("create_component", {"name": "SubAssembly_A"})
    """

@command()
def list_components(app):
    """
    Lists all top-level component occurrences in the design.

    Returns:
        dict: {"components": [{"name": str, "occurrence_name": str, "is_visible": bool}, ...]}

    Examples:
        call_addin("list_components", {})
    """
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
    """
    Renames a component in the design.

    Args:
        old_name (str): Current name of the component.
        new_name (str): New name for the component.

    Examples:
        call_addin("rename_component", {"old_name": "Part1", "new_name": "Chassis"})
    """
    design = get_active_design(app)
    for comp in design.allComponents:
        if comp.name == old_name:
            comp.name = new_name
            return {"message": f"Renamed component '{old_name}' to '{new_name}'"}
    raise Exception(f"Component '{old_name}' not found.")

@command()
def delete_component(app, occurrence_name):
    """
    Deletes a component occurrence from the root assembly.

    Args:
        occurrence_name (str): The name of the occurrence to delete.

    Examples:
        call_addin("delete_component", {"occurrence_name": "Part1:1"})
    """
    design = get_active_design(app)
    rootComp = design.rootComponent
    occ = rootComp.occurrences.itemByName(occurrence_name)
    if not occ:
        raise Exception(f"Component occurrence '{occurrence_name}' not found in root.")
    occ.deleteMe()
    return {"message": f"Deleted component instance '{occurrence_name}'"}

@command()
def create_joint(app, name, component1_name, component2_name, joint_type="rigid", offset_x=0, offset_y=0, offset_z=0):
    """
    Creates a joint between the origins of two components.
    
    Joints define the relative motion and position of parts.

    Args:
        name (str): Name for the joint feature.
        component1_name (str): Name of the first component.
        component2_name (str): Name of the second component.
        joint_type (str): 'rigid', 'revolute', 'slider', 'cylindrical', 'pin_slot', 'planar', 'ball'.
        offset_z (float): Optional Z-offset for the joint (cm).

    Examples:
        # Create a sliding joint between a piston and a cylinder
        call_addin("create_joint", {
            "name": "PistonJoint", 
            "component1_name": "Piston", 
            "component2_name": "Cylinder", 
            "joint_type": "slider"
        })
    """
    design = get_active_design(app)
    root = design.rootComponent
    occ1 = find_occ(app, component1_name)
    occ2 = find_occ(app, component2_name)
    joints = root.joints
    Geo0 = adsk.fusion.JointGeometry.createByPoint(occ1.component.originConstructionPoint)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2.component.originConstructionPoint)
    jointInput = joints.createInput(Geo0, geo1)
    jt = joint_type.lower()
    
    # Configure joint motion
    if jt == "rigid":
        jointInput.setAsRigidJointMotion()
    elif jt == "revolute":
        jointInput.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "slider":
        jointInput.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "cylindrical":
        jointInput.setAsCylindricalJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "pin_slot":
        jointInput.setAsPinSlotJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection, adsk.fusion.JointDirections.XAxisJointDirection)
    elif jt == "planar":
        # Planar joints typically need a normal direction (primary axis) mapping
        jointInput.setAsPlanarJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "ball":
        jointInput.setAsBallJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection, adsk.fusion.JointDirections.XAxisJointDirection)
    else:
        raise ValueError(f"Unsupported joint type: {joint_type}")
        
    if offset_x != 0 or offset_y != 0 or offset_z != 0:
        # Fusion's joint offset is scalar along the joint axis, not a 3D vector.
        offset_value = offset_z if offset_z != 0 else math.sqrt(offset_x**2 + offset_y**2 + offset_z**2)
        jointInput.offset = adsk.core.ValueInput.createByReal(offset_value)
    joint = joints.add(jointInput)
    joint.name = name
    return {"message": f"Created {joint_type} joint '{name}'.", "joint_name": joint.name}

@command()
def create_as_built_joint(app, name, component1_name, component2_name, joint_type="rigid"):
    """
    Creates an 'As-Built' joint between two components in their current positions.
    
    Used when parts are already modeled in their final assembled positions.

    Args:
        name (str): Name for the joint.
        component1_name (str): First component.
        component2_name (str): Second component.
        joint_type (str): Same as create_joint.

    Examples:
        call_addin("create_as_built_joint", {
            "name": "RigidFix", 
            "component1_name": "Base", 
            "component2_name": "Mount"
        })
    """
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
    elif jt == "slider":
        jointInput.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "cylindrical":
        jointInput.setAsCylindricalJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "pin_slot":
        jointInput.setAsPinSlotJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection, adsk.fusion.JointDirections.XAxisJointDirection)
    elif jt == "planar":
        jointInput.setAsPlanarJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif jt == "ball":
        jointInput.setAsBallJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection, adsk.fusion.JointDirections.XAxisJointDirection)
    else:
        raise ValueError(f"Unsupported joint type: {joint_type}")
        
    joint = joints.add(jointInput)
    joint.name = name
    return {"message": f"Created as-built {joint_type} joint '{name}'.", "joint_name": joint.name}
