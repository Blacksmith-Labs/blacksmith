import json
from tenacity import retry, stop_after_attempt
from blacksmith.llm import llm_call
from blacksmith.tools import use_tool
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

    def process(self, messages, query):
        func_calls = []

        @retry(stop=stop_after_attempt(self.max_loops))
        def _think():
            resp = llm_call(messages=messages)

            iterations = 0
            while True:
                print("Iteration ", iterations)
                print(resp)

                content = resp.get("content")
                if content and ("Final Answer:" in content):
                    print(messages)
                    final_answer_index = content.index("Final Answer:") + len("Final Answer:")
                    final_answer = content[final_answer_index:].strip()
                    return final_answer

                func = resp.get("function_call")
                if func:
                    tool_name = func["name"]
                    args = json.loads(func["arguments"])
                    # The port is 5000 locally, 80 for k8s, create a function to do this dynamically
                    data = use_tool(tool_name=tool_name, args=args)
                    print(f"Executed function {tool_name}. Result: {data}")
                    func_calls.append(
                        {
                            "execution_order": iterations,
                            "function_name": {tool_name},
                            "params": {func["arguments"]},
                            "result": {json.dumps(data)},
                        }
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": f"""
                                Result of {tool_name} is {data}.
                                Generate an observation based on this result.
                                If you have enough information to answer {query}, return the final answer prefixed with 'Final Answer:'.
                                Otherwise, based on this observation, proceed with other function calls to gather information as appropriate.
                            """,
                        }
                    )
                resp = llm_call(messages=messages)
                iterations += 1

        return _think(), func_calls

    def run(self, input: str) -> None:
        formatted_prompt = self.prompt.format(input=input)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": formatted_prompt},
        ]
        return self.process(messages=messages, query=input)
