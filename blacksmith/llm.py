import openai
import os


# TODO: Only load functions if called from an "agent"
def llm_call(messages, tools):
    MODEL = os.getenv("MODEL")
    TEMPERATURE = int(os.getenv("TEMPERATURE"))
    return openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        functions=tools,
    )["choices"][0]["message"]
