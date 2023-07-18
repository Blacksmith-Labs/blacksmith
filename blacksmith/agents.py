import threading
import uvicorn
import os
from fastapi import FastAPI, Request


def agent():
    def decorator(cls):
        class Agent(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        agent = Agent()
        app = FastAPI()

        def server():
            @app.get("/")
            async def run(request: Request):
                args = await request.json()
                return agent.run(**args)

            return threading.Thread(target=run_server, kwargs={"app": app})

        server().start()
        return server

    return decorator


def run_server(app):
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT")))
