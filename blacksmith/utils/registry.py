import json
import requests
from blacksmith.utils.tools import tool_to_json_func


class ToolRegistry:
    def __init__(self) -> None:
        self.tools = {}

    def register_tool(self, name, func, description, params):
        try:
            tool_json_str = tool_to_json_func(
                description=description, func=func, params_desc=params
            )
            self.tools[name] = tool_json_str
            print(f"Successfully registered {description}")
        except Exception as e:
            print(f"Error: {e}")

    def get_tools(self):
        return self.tools

    def use_tool(self, tool_name, args):
        pass


registry = ToolRegistry()
