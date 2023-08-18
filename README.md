![blacksmith](images/bs.png)

# Table of Contents
1. [Quickstart](#quickstart)
    - [Configuration](#configuration)
2. [Usage](#usage)
    - [Context Manager](#context-manager)
    - [Classification](#classification)
    - [Schema Guided Generation](#schema-guided-generation)
3. [Function Calls](#function-calls)
    - [Creating Functions](#creating-functions)
    - [Function Calls](#function-calls-1)
4. [Roadmap](#roadmap)
    - [Integrations](#drop-in-integrations)
    - [Primitives](#primitives)

# Quickstart

### Configuration
Set the default configuration for LLM calls.

```python
from blacksmith.context import Config

cfg = Config(
    model="gpt-4-0613",
    temperature=0.1,
    api_key="sk-XXXXXXXXXXXXXXXXXXXXXXXX",
)
```

```python
from blacksmith.llm import Conversation

c = Conversation()

response = c.ask("What is the meaning of life?")
```


# Usage

### Context Manager
We can use the context manager to execute code blocks with an arbitrary configuration.

```python
from blacksmith.context import model

with model("gpt-3.5-turbo", 0.5):
    # All functions in this context are executed with GPT-3.5

    cities = Choice(options=["San Francisco", "Los Angeles", "New York City"])
    print(generate_from(cities, "The Golden Gate Bridge"))
```

### Classification
We can use the `Choice` class to reduce the completion between multiple possibilities.

```python
from blacksmith.llm import Choice, generate_from

cities = Choice(options=["San Francisco", "Los Angeles", "New York City"])
print(generate_from(cities, "The Golden Gate Bridge"))
"""
San Francisco
"""

numbers = Choice(options=[1, 25, 50, 100])
print(generate_from(numbers, "A number greater than 75"))
"""
100
"""

fruits = Choice(options=["Strawberry", "Banana", "Blueberry"])
print(generate_from(fruits, "A red colored fruit"))
"""
Strawberry
"""
```

### Schema Guided Generation
You can generate a JSON mapping to a custom `Schema`.

```python
from blacksmith.llm import Schema, generate_from
from enum import Enum


class City(str, Enum):
    SF = "San Francisco"
    LA = "Los Angeles"
    NYC = "New York City"


class School(str, Enum):
    CAL = "UC Berkeley"
    STANFORD = "Stanford"
    UCLA = "UCLA"


class Character(Schema):
    name: str
    age: int
    school: School
    city: City

print(
    generate_from(Character, "John just graduated from UC Berkeley and lives near Golden Gate Park in SF")
)
"""
{'name': 'John', 'age': 22, 'school': 'UC Berkeley', 'city': 'San Francisco'}
"""
```

# Function Calls

### Creating functions
We can create functions for our LLM to call using the `tool` decorator.

```python
from blacksmith.tools import tool

@tool(
    name="foo",
    description="A function that returns the parameter passed to it",
    params={"bar": "The return value"},
)
def foo(bar: str):
    return bar
```

### Function calls

We can execute function calls from the result of `ask`.

```python
from blacksmith.tools import tool
from blacksmith.llm import Conversation


@tool(
    name="Multiply",
    description="A function that returns the result of the first argument multiplied by the second argument",
    params={"a": "The first number", "b": "The second number"},
)
def multiply(a: int, b: int):
    return a * b


c = Conversation()
resp = c.ask("What is 5 * 10")

if resp.has_function_call():
    # We can inspect the function call if we want
    resp.function_call.inspect()
    """
    {
        "tool": "Multiply",
        "args": {
            "a": 5,
            "b": 10
        }
    }
    """

    # Looks good!
    result = resp.execute_function_call()

    # We can inspect the result if we want
    result.inspect()
    """
    {
        "tool": "Multiply",
        "args": {
            "a": 5,
            "b": 10
        },
        "result": 50
    }
    """
    resp = c.continue_from_result(result, stop=True)

# Final answer
print(resp.content)
"""
50
"""
```

# Roadmap

### Drop-in integrations

- [x] `OpenAI`
- [ ] `Anthropic`
- [ ] `llama-2`
- [ ] `HuggingFace` and `Replicate` models

### Primitives

- [ ] Embeddings
- [ ] Prompting
- [ ] Agents