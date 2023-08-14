import openai
import json
from typing import Optional, List, Any
from blacksmith.config.constants import ChatRoles
from blacksmith.config.prompts import DEFAULT_OBSERVATION
from blacksmith.config.environment import MODEL, TEMPERATURE
from blacksmith.utils.registry import registry
from blacksmith.tools import use_tool
from pydantic import BaseModel


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
    args: str | None

    def execute(self, debug: bool = False):
        """
        Execute the function call generated by the language model and return the resulting value.
        """
        try:
            tool_result = use_tool(tool_name=self.tool, args=json.loads(self.args))
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

    def ask(
        self, prompt: str, role: ChatRoles = ChatRoles.USER, debug: bool = False
    ) -> LLMResponse:
        """
        Sends a prompt (optional) plus the current message chain to the language model.
        You can change the role by passing in a ChatRoles parameter (defaults to User).
        Returns a LLMResponse object.
        """

        # initialize messages
        if self.system_prompt and not self.messages:
            self.messages = [ChatMessage(role=ChatRoles.SYSTEM, content=self.system_prompt)]

        self.add_message(ChatMessage(role=role, content=prompt))

        return self._send(debug=debug)

    def _send(self, debug=False) -> LLMResponse:
        # OpenAI
        tools = registry.get_tools()
        try:
            if MODEL == "musabgultekin/functionary-7b-v1":
                openai.api_base = "https://0xalec--functionary-fastapi-app-dev.modal.run/v1"
            res = openai.ChatCompletion.create(
                model=MODEL,
                messages=[message.model_dump() for message in self.messages],
                temperature=TEMPERATURE,
                functions=tools,
            )["choices"][0]["message"]

            res = res.to_dict()
            if debug:
                print(res)

            fc = res.get("function_call")

            if fc:
                fc = fc.to_dict()
            return LLMResponse(
                content=res.get("content"),
                function_call=FunctionCall(tool=fc.get("name"), args=fc.get("arguments"))
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

    def continue_from_result(self, fcr: FunctionCallResult):
        """
        Generates an observation from a function call result and sends another request to the LLM.
        """
        observation = fcr.generate_observation()
        self.add_message(observation)
        return self._send()
