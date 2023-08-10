import openai
import json
from blacksmith.config.environment import MODEL, TEMPERATURE, MAX_TOKENS
from blacksmith.config.constants import OPEN_SOURCE_MODELS
from blacksmith.utils.registry import registry
from blacksmith.tools import use_tool


def llm_call(prompt="", messages=[], streaming=False, auto_use_tool=False, verbose=False):
    global MODEL
    match MODEL:
        case "gpt-3.5-turbo":
            # OpenAI
            tools = registry.get_tools()
            res = openai.ChatCompletion.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                functions=tools,
            )["choices"][0]["message"]
            func = res.get("function_call")
            if func and auto_use_tool:
                if verbose:
                    print(f"Calling {func['name']} with {func['arguments']}")
                tool_result = use_tool(tool_name=func["name"], args=json.loads(func["arguments"]))
                return tool_result
            return res["content"]
