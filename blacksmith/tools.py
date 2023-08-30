import json
from blacksmith.utils.tools import tool_to_json_func


class ToolRegistry:
    def __init__(self) -> None:
        self.tools = {}
        self.funcs = {}

    def register_tool(self, name, func, description, params):
        try:
            tool_json_str = tool_to_json_func(
                name=name, description=description, func=func, params_desc=params
            )
            self.tools[name] = tool_json_str
            self.funcs[name] = func
        except Exception as e:
            print(f"Error registering {name}: {e}")

    def get_tools(self) -> list[str]:
        return [json.loads(v) for v in self.tools.values()]

    def use_tool(self, tool_name, args):
        func = self.funcs[tool_name]
        return func(**args)


registry = ToolRegistry()


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
