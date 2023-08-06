import openai
from llmengine import Completion
from blacksmith.config.environment import MODEL, TEMPERATURE, MAX_TOKENS
from blacksmith.config.constants import OPEN_SOURCE_MODELS
from blacksmith.utils.registry import registry


def llm_call(prompt="", messages=[], streaming=False):
    global MODEL
    match MODEL:
        case "gpt-3.5-turbo":
            # OpenAI
            tools = registry.get_tools()
            return openai.ChatCompletion.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                functions=tools,
            )["choices"][0]["message"]
        case MODEL if MODEL in OPEN_SOURCE_MODELS:
            # Scale
            resp = Completion.create(
                model=MODEL,
                temperature=TEMPERATURE,
                max_new_tokens=MAX_TOKENS,
                prompt=prompt,
                stream=streaming,
            )
            if streaming:
                return resp
            return resp.output.text
        case other:
            # throw an error here
            pass
