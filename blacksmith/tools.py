import uvicorn
from fastapi import FastAPI, Request
import threading
import functools
import os
import redis
import json
import inspect

# TODO: Update this to support more types
type_mappings = {"str": "string", "int": "integer"}


def _tool_to_json_func(description, func, params_desc):
    func_parameters = _get_function_parameters(func=func)
    properties = {}
    for func_parameter in func_parameters:
        param_name, param_type = func_parameter.items()
        properties.update(
            {
                param_name[1]: {
                    "type": type_mappings[param_type[1].__name__],
                    "description": params_desc[param_name[1]],
                }
            },
        )
    return {
        "name": os.getenv("TOOL_SERVICE_NAME"),
        "description": description,
        "parameters": {"type": "object", "properties": properties, "required": []},
    }


def _get_function_parameters(func):
    parameters = []
    signature = inspect.signature(func)
    for param in signature.parameters.values():
        param_info = {
            "name": param.name,
            "type": param.annotation if param.annotation != inspect.Parameter.empty else None,
        }
        parameters.append(param_info)
    return parameters


def tool(description, params):
    def decorator(func):
        # Start FastAPI and Redis
        app = FastAPI()
        r = redis.Redis(host="redis-service", port=6379)

        # Register the tool
        try:
            tool_json_str = json.dumps(
                _tool_to_json_func(description=description, func=func, params_desc=params)
            )
            r.rpush("tools", tool_json_str)
            print(f"Successfully registered {description}")
        except Exception as e:
            print(f"Error: {e}")

        # Close redis connection
        r.close()

        @functools.wraps(func)
        def wrapper():
            # Register the function as an endpoint in FastAPI
            # TODO: Wrap this in a try/except block
            @app.get("/")
            async def entry(request: Request):
                body = await request.json()
                return func(**body)

            return threading.Thread(target=run_server, kwargs={"app": app})

        wrapper().start()
        return wrapper

    return decorator


def run_server(app):
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT")))
