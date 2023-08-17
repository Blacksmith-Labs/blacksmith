
# Usage

### Classification
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

### Configuration
We can set a default configuration for LLM calls.

```python
from blacksmith.context import Config

cfg = Config(
    model="gpt-4-0613",
    temperature=0.1,
    api_key="sk-XXXXXXXXXXXXXXXXXXXXXXXX",
)

# GPT-4 with temperature set to 0.1
cities = Choice(options=["San Francisco", "Los Angeles", "New York City"])
print(generate_from(cities, "The Golden Gate Bridge"))
```

### Context Manager
We can also use the context manager to execute code blocks under a different configuration.

```python
from blacksmith.context import model

with model("gpt-3.5-turbo", 0.5):
    # All functions in this context are executed with GPT-3.5

    cities = Choice(options=["San Francisco", "Los Angeles", "New York City"])
    print(generate_from(cities, "The Golden Gate Bridge"))
```