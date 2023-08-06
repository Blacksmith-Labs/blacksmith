import redis
import json
from blacksmith.config.constants import REGISTRY_CONTAINER_NAME
from blacksmith.utils.tools import tool_to_json_func


class ToolRegistry:
    def __init__(self) -> None:
        self.r = redis.Redis(host=REGISTRY_CONTAINER_NAME, port=6379)

    def __del__(self) -> None:
        self.r.close()

    def register_tool(self, func, description, params):
        # Register the tool
        try:
            tool_json_str = tool_to_json_func(
                description=description, func=func, params_desc=params
            )
            self.r.rpush("tools", tool_json_str)
            print(f"Successfully registered {description}")
        except Exception as e:
            print(f"Error: {e}")

    def get_tools(self):
        tools = [json.loads(tool.decode()) for tool in self.r.lrange("tools", 0, -1)]
        return tools


registry = ToolRegistry()
