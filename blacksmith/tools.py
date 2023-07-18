import uvicorn
from fastapi import FastAPI, Request
import threading
import functools
import os
from blacksmith.utils.tools import parse_tool_from_args, register_tool


def tool(name, description, params):
    # Parse the tool name from sysargs
    tool_name = parse_tool_from_args()

    def decorator(func):
        # Only run business logic for target tool functions
        if name != tool_name:
            return func

        # Start FastAPI and Redis
        app = FastAPI()

        register_tool(func=func, description=description, params=params)

        # Spin up the microservice
        @functools.wraps(func)
        def server():
            @app.get("/")
            async def entry(request: Request):
                # TODO: Wrap this in a try/except block
                body = await request.json()
                return func(**body)

            return threading.Thread(target=run_server, kwargs={"app": app})

        server().start()
        return server

    return decorator


def run_server(app):
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT")))
