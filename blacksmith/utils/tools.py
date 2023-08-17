import os
import json
import inspect
import argparse
from blacksmith.config.constants import TYPE_MAPPINGS


def tool_to_json_func(name, description, func, params_desc):
    func_parameters = _get_function_parameters(func=func)
    properties = {}
    for func_parameter in func_parameters:
        param_name, param_type = func_parameter.items()
        properties.update(
            {
                param_name[1]: {
                    "type": TYPE_MAPPINGS[param_type[1].__name__],
                    "description": params_desc[param_name[1]],
                }
            },
        )
    return json.dumps(
        {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": []},
        }
    )


def _get_function_parameters(func):
    parameters = []
    signature = inspect.signature(func)
    for param in signature.parameters.values():
        param_info = {
            "name": param.name,
            "type": param.annotation if param.annotation != inspect.Parameter.empty else None,
        }
        parameters.append(param_info)
    return parameters


def parse_tool_from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", help="Specify the tool name")
    args = parser.parse_args()
    tool_name = args.tool
    return tool_name
