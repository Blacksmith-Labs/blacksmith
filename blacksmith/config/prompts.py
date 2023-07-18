DEFAULT_SYSTEM_PROMPT = """
**Instructions:**

1. Provide a clear and concise description of your question or request.
2. Include any relevant details or context that can help the model understand your prompt.
3. If applicable, specify the desired format or structure for the response.
4. Feel free to ask follow-up questions or provide additional instructions as needed.

**Prompt:**
"""

DEFAULT_REACT_PROMPT = """
Answer the following questions as best you can.
If the user demands a final answer but you are unsure, consider executing a function call to gather more information.

The result of all previous function calls will be added to the conversation history as an observation.

Begin!

Question: {input}

Decompose the question into multiple subquestions, and answer each one individually in order to arrive at the final answer.
"""
