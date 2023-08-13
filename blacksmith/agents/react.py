from blacksmith.llm import Conversation
from blacksmith.config.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_REACT_PROMPT


# ReAct: Synergizing Reasoning and Acting in Language Models - https://arxiv.org/abs/2210.03629
class ReActAgent:
    def __init__(self, **kwargs) -> None:
        type = kwargs.get("type", "zero-shot-react")

        # Make this a switch case
        if type == "zero-shot-react":
            self.prompt = DEFAULT_REACT_PROMPT
            self.system_prompt = DEFAULT_SYSTEM_PROMPT
        else:
            self.prompt = kwargs.get("prompt")
            self.system_prompt = kwargs.get("system_prompt")

        self.max_loops = kwargs.get("max_loops", 5)

    def run(self, input: str) -> None:
        c = Conversation(system_prompt=self.system_prompt)
        response = c.ask(prompt=self.prompt.format(input=input))

        # We know the agent is done when we have a 'content' parameter
        while response.has_function_call():
            # Execute the function call
            result = response.execute_function_call()

            # Let's continue the conversation see if we have enough info to answer the original question.
            response = c.continue_from_result(result)
        return response.content
