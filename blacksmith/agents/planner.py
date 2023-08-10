import asyncio
import openai
from typing import List, Generator
from pydantic import Field, BaseModel
from openai_function_call import OpenAISchema
from blacksmith.tools import get_tools
from blacksmith.llm import llm_call


class TaskResult(BaseModel):
    task_id: int
    question: str
    result: str


class TaskResults(BaseModel):
    results: List[TaskResult]


class Task(OpenAISchema):
    """
    Class representing a single task in a task plan.
    """

    id: int = Field(..., description="Unique id of the task")
    task: str = Field(
        ...,
        description="""Contains the task in text form. If there are multiple tasks, 
        this task can only be executed when all dependant subtasks have been answered.""",
    )
    subtasks: List[int] = Field(
        default_factory=list,
        description="""List of the IDs of subtasks that need to be answered before 
        we can answer the main question. Use a subtask when anything may be unknown 
        and we need to ask multiple questions to get the answer. 
        Dependencies must only be other tasks.""",
    )

    async def aexecute(self, with_results: TaskResults) -> TaskResult:
        """
        Executes the task by asking the question and returning the answer.
        """

        messages = []
        if with_results.results:
            for task_result in with_results.results:
                self.task = self.task.replace(f"{{{task_result.task_id}}}", f"{task_result.result}")
        messages.append({"role": "user", "content": f"{self.task}"})
        result = llm_call(messages=messages, auto_use_tool=True, verbose=True)
        return TaskResult(task_id=self.id, question=self.task, result=f"{result}")


class TaskPlan(OpenAISchema):
    """
    Container class representing a tree of tasks and subtasks.
    Make sure every task is in the tree, and every task is done only once.
    """

    task_graph: List[Task] = Field(
        ...,
        description="List of tasks and subtasks that need to be done to complete the main task. Consists of the main task and its dependencies.",
    )

    def _get_execution_order(self) -> List[int]:
        """
        Returns the order in which the tasks should be executed using topological sort.
        Inspired by https://gitlab.com/ericvsmith/toposort/-/blob/master/src/toposort.py
        """
        tmp_dep_graph = {item.id: set(item.subtasks) for item in self.task_graph}

        def topological_sort(dep_graph: dict[int, set[int]]) -> Generator[set[int], None, None]:
            while True:
                ordered = set(item for item, dep in dep_graph.items() if len(dep) == 0)
                if not ordered:
                    break
                yield ordered
                dep_graph = {
                    item: (dep - ordered) for item, dep in dep_graph.items() if item not in ordered
                }
            if len(dep_graph) != 0:
                raise ValueError(
                    f"Circular dependencies exist among these items: {{{', '.join(f'{key}:{value}' for key, value in dep_graph.items())}}}"
                )

        result = []
        for d in topological_sort(tmp_dep_graph):
            result.extend(sorted(d))
        return result

    async def execute(self) -> dict[int, TaskResult]:
        """
        Executes the tasks in the task plan in the correct order using asyncio and chunks with answered dependencies.
        """
        execution_order = self._get_execution_order()
        tasks = {q.id: q for q in self.task_graph}
        task_results = {}
        while True:
            ready_to_execute = [
                tasks[task_id]
                for task_id in execution_order
                if task_id not in task_results
                and all(subtask_id in task_results for subtask_id in tasks[task_id].subtasks)
            ]
            # prints chunks to visualize execution order
            print(f"Executing: {ready_to_execute}")
            computed_answers = await asyncio.gather(
                *[
                    q.aexecute(
                        with_results=TaskResults(
                            results=[
                                result
                                for result in task_results.values()
                                if result.task_id in q.subtasks
                            ]
                        )
                    )
                    for q in ready_to_execute
                ]
            )
            for answer in computed_answers:
                task_results[answer.task_id] = answer
            from pprint import pprint

            pprint(task_results)
            if len(task_results) == len(execution_order):
                break
        return task_results


# Task.model_rebuild()
# TaskPlan.model_rebuild()


def task_planner(question: str) -> TaskPlan:
    messages = [
        {
            "role": "system",
            "content": "You are a world class query planning algorithm capable of breaking apart questions into its depenencies queries such that the answers can be used to inform the parent question. Do not answer the questions, simply provide correct compute graph with good specific questions to ask and relevant dependencies. Before you call the function, think step by step to get a better understanding the problem.",
        },
        {
            "role": "user",
            "content": f"""Question: {question}\n Generate the correct query plan with consideration to the available tools.\n
            You have access to the following tools: {[{'name': tool['name'], 'description': tool['description']} for tool in get_tools()]}\n
            Use the task ID as a placeholder if you need the result of a dependency to generate a task question.
            Example:
            'Use the compare-tool to compare {{1}} and {{2}}'
            """,
        },
    ]

    # We need GPT-4 here
    completion = openai.ChatCompletion.create(
        model="gpt-4-0613",
        temperature=0,
        functions=[TaskPlan.openai_schema],
        function_call={"name": TaskPlan.openai_schema["name"]},
        messages=messages,
        max_tokens=1000,
    )
    root = TaskPlan.from_response(completion)

    return root


class QueryPlannerAgent:
    def __init__(self) -> None:
        pass

    def create_plan(self, question: str) -> TaskPlan:
        return task_planner(question=question)
