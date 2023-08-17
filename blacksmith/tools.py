import os
from blacksmith.utils.registry import registry


def tool(name, description, params):
    def decorator(func):
        registry.register_tool(name=name, func=func, description=description, params=params)

    return decorator


def use_tool(tool_name: str, args: dict):
    """
    Make an API request to a tool.
    tool_name should be a string corresponding to the container name of the tool being called
    args should be a Python Dictionary object
    """
    return registry.use_tool(tool_name=tool_name, args=args)


def get_tools():
    return registry.get_tools()
