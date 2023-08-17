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
