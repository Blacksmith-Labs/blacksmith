import redis
import json
import requests
from tenacity import retry, stop_after_attempt
from blacksmith.llm import llm_call
from blacksmith.config.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_REACT_PROMPT

# Connect to tool storage service
# We should expose an SDK to create a client and manually retrieve tools if user has their own Agent implementation
r = redis.Redis(host="redis-service", port=6379)


class Agent:
    def __init__(self, **kwargs) -> None:
        type = kwargs.get("type", "zero-shot-react")

        # Make this a switch case
        if type == "zero-shot-react":
            self.prompt = DEFAULT_REACT_PROMPT
            self.system_prompt = DEFAULT_SYSTEM_PROMPT
        else:
            self.prompt = kwargs.get("prompt")
            self.system_prompt = kwargs.get("system_prompt")

        self.tools = kwargs.get(
            "tools", [json.loads(tool.decode()) for tool in r.lrange("tools", 0, -1)]
        )
        self.max_loops = kwargs.get("max_loops", 5)

    def process(self, messages, query):
        func_calls = []

        @retry(stop=stop_after_attempt(self.max_loops))
        def _think():
            resp = llm_call(messages=messages, tools=self.tools)

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
                    service_name = func["name"]
                    args = json.loads(func["arguments"])
                    url = f"http://{service_name}:80"
                    tool_res = requests.get(url=url, json=args)
                    data = tool_res.json()
                    print(f"Executed function {service_name}. Result: {data}")
                    func_calls.append(
                        {
                            "execution_order": iterations,
                            "function_name": {service_name},
                            "params": {func["arguments"]},
                            "result": {json.dumps(data)},
                        }
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": f"""
                                Result of {service_name} is {data}.
                                Generate an observation based on this result.
                                If you have enough information to answer {query}, return the final answer prefixed with 'Final Answer:'.
                                Otherwise, based on this observation, proceed with other function calls to gather information as appropriate.
                            """,
                        }
                    )
                resp = llm_call(messages=messages, tools=self.tools)
                iterations += 1

        return _think(), func_calls

    def run(self, input: str) -> None:
        formatted_prompt = self.prompt.format(input=input)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": formatted_prompt},
        ]
        return self.process(messages=messages, query=input)
