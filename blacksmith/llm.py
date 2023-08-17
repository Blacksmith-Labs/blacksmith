import openai
import json
import os
from typing import Optional, List, Any
from blacksmith.config.constants import ChatRoles
from blacksmith.config.prompts import DEFAULT_OBSERVATION
from blacksmith.config.constants import TYPE_MAPPINGS
from blacksmith.context import Config
from blacksmith.utils.registry import registry
from blacksmith.tools import use_tool
from pydantic import BaseModel


# Code from https://github.com/jxnl/instructor
def _remove_a_key(d, remove_key) -> None:
    """Remove a key from a dictionary recursively"""
    if isinstance(d, dict):
        for key in list(d.keys()):
            if key == remove_key:
                del d[key]
            else:
                _remove_a_key(d[key], remove_key)


class Schema(BaseModel):
    # Code from https://github.com/jxnl/instructor
    @classmethod
    @property
    def schema(cls):
        schema = cls.model_json_schema()
        parameters = {k: v for k, v in schema.items() if k not in ("title", "description")}
        parameters["required"] = sorted(
            k for k, v in parameters["properties"].items() if not "default" in v
        )

        _remove_a_key(parameters, "additionalProperties")
        _remove_a_key(parameters, "title")

        return {
            "name": schema["title"],
            "description": "Complete the function call with the choices given.",
            "parameters": parameters,
        }


class Choice(Schema):
    options: List[Any]

    # We over-ride the `schema()` method from the parent class
    # Unfortunately, this needs to be an instance method as the option type is not known until runtime
    def schema(cls):
        model = cls.model_dump()
        option_type = TYPE_MAPPINGS[type(model["options"][0]).__name__]
        return {
            "name": "Choice",
            "description": "Complete the function call with the choices given.",
            "parameters": {
                "type": "object",
                "properties": {
                    "choice": {"type": option_type, "enum": [v for v in model["options"]]}
                },
            },
        }


def generate_from(obj: Schema, query: str):
    is_choice = isinstance(obj, Choice)
    object_schema = obj.schema() if is_choice else obj.schema

    c = Conversation(
        system_prompt="You are a helpful assistant who only has access to a single function."
    )
    resp = c.ask(query, functions=[object_schema], function_call={"name": object_schema["name"]})
    response = json.loads(resp.function_call.args)
    return response if not is_choice else response["choice"]


class ChatMessage(BaseModel):
    role: ChatRoles
    content: str

    class Config:
        use_enum_values = True


class FunctionCall(BaseModel):
    """
    A class representing a function call generated from a LLM.
    """

    tool: str | None
    args: dict | None

    def inspect(self):
        """
        Prints the JSON representation of FunctionCall to stdout.
        """
        json = self.model_dump_json(indent=4)
        print(json)

    def execute(self, debug: bool = False):
        """
        Execute the function call generated by the language model and return the resulting value.
        """
        try:
            tool_result = use_tool(tool_name=self.tool, args=self.args)
            if debug:
                print(f"Calling {self.tool} with {self.args}", flush=True)
                print("Result of function call:", tool_result, flush=True)
            return FunctionCallResult(tool=self.tool, args=self.args, result=tool_result)
        except Exception as e:
            print(f"Error executing {self.tool}: {e}", flush=True)


class FunctionCallResult(FunctionCall):
    """
    A class representing the result of calling a LLM function.
    """

    result: Any = None

    def generate_observation(self, observation_prompt: str = DEFAULT_OBSERVATION) -> ChatMessage:
        """
        Generates a ChatModelMessage as an observation of the result of tool usage.
        You can override the default observation prompt by passing in an observation_prompt parameter.
        """
        return ChatMessage(
            role=ChatRoles.USER,
            content=observation_prompt.format(result=self.result, tool=self.tool, args=self.args),
        )


class LLMResponse(BaseModel):
    content: str | None
    function_call: Optional[FunctionCall] = None

    def execute_function_call(self, debug: bool = False) -> FunctionCallResult:
        if not self.function_call:
            return ValueError("Function call not found")
        return self.function_call.execute(debug=debug)

    def has_function_call(self) -> bool:
        return self.function_call is not None


class Conversation(BaseModel):
    """
    Class representing a conversation with a language model.
    """

    system_prompt: Optional[str] = ""
    messages: Optional[List[ChatMessage]] = []
    config: Optional[Config] = None

    def ask(
        self,
        prompt: str,
        functions: list[dict] = [],
        function_call: str | dict = "auto",
        role: ChatRoles = ChatRoles.USER,
        debug: bool = False,
    ) -> LLMResponse:
        """
        Sends a prompt (optional) plus the current message chain to the language model.
        You can change the role by passing in a ChatRoles parameter (defaults to User).
        Returns a LLMResponse object.
        """

        # init config
        # this cannot be defaulted since we need `model_post_init` to be called after the first instantiation
        if not self.config:
            self.config = Config()
            self.config.load()

        # initialize messages
        if self.system_prompt and not self.messages:
            self.messages = [ChatMessage(role=ChatRoles.SYSTEM, content=self.system_prompt)]

        # default to all available functions
        if not functions:
            functions = registry.get_tools()

        self.add_message(ChatMessage(role=role, content=prompt))

        return self._send(functions=functions, function_call=function_call, debug=debug)

    def _send(
        self, functions: list[dict], function_call: str | dict = "auto", debug=False
    ) -> LLMResponse:
        # OpenAI

        if not functions:
            res = openai.ChatCompletion.create(
                model=self.config.model,
                messages=[message.model_dump() for message in self.messages],
                temperature=self.config.temperature,
            )["choices"][0]["message"]
            return LLMResponse(content=res.get("content"))
        try:
            openai.api_key = self.config.api_key
            res = openai.ChatCompletion.create(
                model=self.config.model,
                messages=[message.model_dump() for message in self.messages],
                temperature=self.config.temperature,
                functions=functions,
                function_call=function_call,
            )["choices"][0]["message"]

            res = res.to_dict()
            if debug:
                print(res)

            fc = res.get("function_call")

            if fc:
                fc = fc.to_dict()
            return LLMResponse(
                content=res.get("content"),
                function_call=FunctionCall(
                    tool=fc.get("name"), args=json.loads(fc.get("arguments"))
                )
                if fc
                else None,
            )
        except Exception as e:
            print(f"Error sending {self.messages}: {e}")

    def add_message(self, message: ChatMessage) -> None:
        """
        Adds a ChatMessage to the message chain.
        """
        self.messages.append(message)

    def continue_from_result(self, fcr: FunctionCallResult, stop: bool = False):
        """
        Generates an observation from a function call result and sends another request to the LLM.
        """
        observation = fcr.generate_observation()
        self.add_message(observation)
        functions = [] if stop else registry.get_tools()
        return self._send(functions=functions)
