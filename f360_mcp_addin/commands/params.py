import adsk.core
import adsk.fusion
from . import command
from .base import get_active_design

@command()
def create_user_parameter(app, name, expression, unit="", description=""):
    design = get_active_design(app)
    userParams = design.userParameters
    param = userParams.add(name, adsk.core.ValueInput.createByString(expression), unit, description)
    return {
        "message": f"Created parameter '{name}' = {expression}",
        "name": param.name,
        "value": round(param.value, 3),
        "comment": param.comment
    }

@command(name="create_parameter")
def create_parameter(app, name, value, comment=""):
    """Compatibility wrapper for E2E tests."""
    return create_user_parameter(app, name, value, description=comment)

@command()
def list_user_parameters(app):
    return list_parameters(app)

@command()
def list_parameters(app):
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
    return update_parameter(app, name, expression, description)

@command()
def delete_user_parameter(app, name):
    design = get_active_design(app)
    param = design.userParameters.itemByName(name)
    if not param:
        raise Exception(f"User parameter '{name}' not found.")
    param.deleteMe()
    return {"message": f"Deleted parameter '{name}'"}
