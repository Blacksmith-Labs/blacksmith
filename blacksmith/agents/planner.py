import asyncio
import openai
from typing import List, Generator
from pydantic import Field, BaseModel
from openai_function_call import OpenAISchema
from blacksmith.tools import get_tools
from blacksmith.llm import Conversation, FunctionCall


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

    def generate_function_call(self, debug: bool = False) -> FunctionCall | None:
        """
        Not every query might be a function call!
        """
        c = Conversation()
        resp = c.ask(prompt=self.task, debug=debug)
        if resp.has_function_call():
            return resp.function_call

    def generate_and_execute_function_call(self, debug: bool = False) -> TaskResult:
        function_call = self.generate_function_call(debug=debug)
        if not function_call:
            return TaskResult(
                task_id=self.id,
                question=self.task,
                result="",
            )
        return TaskResult(
            task_id=self.id,
            question=self.task,
            result=str(function_call.execute(debug=debug).result),
        )


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

    def get_ready_to_execute(self):
        execution_order = self._get_execution_order()
        tasks = {q.id: q for q in self.task_graph}
        task_results = {}
        return [
            tasks[task_id]
            for task_id in execution_order
            if task_id not in task_results
            and all(subtask_id in task_results for subtask_id in tasks[task_id].subtasks)
        ]

    def execute_current_level(self, debug: bool = False) -> dict[int, TaskResult]:
        """
        Executes the current dependency level of the graph.

        This will return the TaskGraph with
        """
        tasks = self.get_ready_to_execute()
        if debug:
            print(f"Executing {tasks}", flush=True)
        task_results = {}

        # Not every task might be a function call!
        # TODO: Implement other execution options for a task
        results = [task.generate_and_execute_function_call() for task in tasks]
        for result in results:
            task_results[result.task_id] = result
        return task_results

    def has_queries(self) -> bool:
        return len(self.task_graph) != 0


def generate_task_plan(question: str) -> TaskPlan:
    messages = [
        {
            "role": "system",
            "content": """
            You are a world class query planning algorithm capable of breaking apart questions into its depenencies queries such that the answers can be used to inform the parent question. Do not answer the questions, simply provide correct compute graph with good specific questions to ask and relevant dependencies.
            Before you call the function, think step by step to get a better understanding the problem.\n
            """,
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


def update_task_plan(question, task_results, debug: bool = False) -> TaskPlan:
    if debug:
        print("Before update:", task_results, flush=True)

    messages = [
        {
            "role": "system",
            "content": """
        You are a world class query planning algorithm capable of breaking apart questions into its depenencies queries such that the answers can be used to inform the parent question. Do not answer the questions, simply provide correct compute graph with good specific questions to ask and relevant dependencies.
        Before you call the function, think step by step to get a better understanding the problem.\n
        """,
        },
        {
            "role": "user",
            "content": f"""
            You previously created a query plan to answer a user question.
            Given the previous query plan (with results), update the query plan given the information gained from the results of executing the current dependency level.
            In your new query plan, do not include previously answered questions from the last query plan.
            
            Original Question:
            {question}
            
            Previous query plan:
            {task_results}
            
            You have access to the following tools: {[{'name': tool['name'], 'description': tool['description']} for tool in get_tools()]}\n
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
    task_plan = TaskPlan.from_response(completion)

    if debug:
        print("After update:", task_plan, flush=True)

    return task_plan


class QueryPlannerAgent:
    def __init__(self) -> None:
        self.task_plan = None
        self.original_question = None
        self.task_results = []

    def create_plan(self, question: str) -> TaskPlan:
        self.task_plan = generate_task_plan(question=question)
        self.original_question = question

    def execute_current_level(self, debug: bool = False) -> dict[int, TaskResult]:
        """
        Executes the current dependency level of the TaskGraph and stores the results.
        """
        tasks = self.task_plan.execute_current_level(debug=debug)
        for task in [task.model_dump() for task in tasks.values()]:
            if task.get("result"):
                self.task_results.append(task)
        return tasks

    def update_plan(self) -> TaskPlan | None:
        """
        Executes the current level and updates the plan.

        This function will return an empty task graph if the query is complete.
        """
        self.task_plan = update_task_plan(
            question=self.original_question, task_results=self.get_completed_tasks()
        )
        return self.task_plan

    def get_completed_tasks(self):
        return self.task_results
