import adsk.core
import adsk.fusion
from . import command
from .base import get_active_design

@command()
def create_user_parameter(app, name, expression, unit="", description=""):
    """
    Creates a new user-defined parameter in the design.
    
    User parameters are key for building flexible, parametric models.

    Args:
        name (str): Unique identifier for the parameter (no spaces).
        expression (str): Value or formula (e.g., "10.5", "Length * 2").
        unit (str, optional): Fusion unit string (e.g., "mm", "deg"). Default is cm-based.
        description (str, optional): Documentation comment for the parameter.

    Examples:
        # Create a basic length parameter
        call_addin("create_user_parameter", {"name": "Width", "expression": "50mm"})
    """

@command(name="create_parameter")
def create_parameter(app, name, value, comment=""):
    """
    Compatibility wrapper for creating a user parameter.

    Args:
        name (str): Parameter identifier.
        value (str): Initial value or expression.
        comment (str, optional): Documentation note.

    Examples:
        call_addin("create_parameter", {"name": "TestParam", "value": "10mm"})
    """
    return create_user_parameter(app, name, value, description=comment)

@command()
def list_user_parameters(app):
    """
    Lists all user-defined parameters.

    Examples:
        call_addin("list_user_parameters", {})
    """
    return list_parameters(app)

@command()
def list_parameters(app):
    """
    Lists all parameters in the design (user-defined and model-based).

    Returns:
        dict: {"parameters": [{"name": str, "expression": str, "value": float, ...}, ...]}

    Examples:
        call_addin("list_parameters", {})
    """
    design = get_active_design(app)
    params_list = []
    for i in range(design.allParameters.count):
        p = design.allParameters.item(i)
        params_list.append({
            "name": p.name,
            "expression": p.expression,
            "value": round(p.value, 3),
            "unit": p.unit,
            "comment": p.comment,
            "isUserParameter": p.isUserParameter
        })
    return {"parameters": params_list}

@command()
def update_parameter(app, name, expression=None, description=None):
    """
    Updates an existing parameter's value or description.

    Args:
        name (str): The name of the parameter to update.
        expression (str, optional): New value or formula.
        description (str, optional): New comment.

    Examples:
        # Change the width to a new value
        call_addin("update_parameter", {"name": "Width", "expression": "75mm"})
    """
    design = get_active_design(app)
    param = design.allParameters.itemByName(name)
    if not param:
        raise Exception(f"Parameter '{name}' not found.")
    if expression is not None:
        param.expression = expression
    if description is not None:
        param.comment = description
    return {
        "message": f"Updated parameter '{name}'",
        "name": param.name,
        "value": round(param.value, 3),
        "comment": param.comment
    }

@command()
def update_user_parameter(app, name, expression=None, description=None):
    """
    Updates an existing user-defined parameter.

    Args:
        name (str): Parameter name.
        expression (str, optional): New value/formula.
        description (str, optional): New comment.

    Examples:
        call_addin("update_user_parameter", {"name": "TestParam", "expression": "20mm"})
    """
    return update_parameter(app, name, expression, description)
    """
    Updates an existing user-defined parameter.

    Args:
        name (str): Parameter name.
        expression (str, optional): New value/formula.
        description (str, optional): New comment.

    Examples:
        call_addin("update_user_parameter", {"name": "TestParam", "expression": "20mm"})
    """
    return update_parameter(app, name, expression, description)

@command()
def delete_user_parameter(app, name):
    """
    Deletes a user-defined parameter.

    Args:
        name (str): The name of the parameter to delete.

    Examples:
        call_addin("delete_user_parameter", {"name": "Width"})
    """
    design = get_active_design(app)
    param = design.userParameters.itemByName(name)
    if not param:
        raise Exception(f"User parameter '{name}' not found.")
    param.deleteMe()
    return {"message": f"Deleted parameter '{name}'"}
