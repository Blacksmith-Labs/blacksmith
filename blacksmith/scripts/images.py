import yaml
import docker


def build_agent_images():
    client = docker.from_env()
    with open("blacksmith.yaml", "r") as f:
        data = yaml.safe_load(f)

    agents = data["agents"]
    agent_specs = []

    for agent in agents:
        file_name = agent["handler"]
        agent_name = agent["name"].lower()  # this needs to be lowercase or k8s will error...
        envars = agent["env"]

        PORT = agent.get("port", 5000)

        model = agent["model"]
        envars.update(
            {
                "MODEL": model["name"],
                "TEMPERATURE": model["temperature"],
                "MAX_TOKENS": model.get("max_tokens", 20),  # optional
                "PORT": PORT,
            }
        )

        dockerfile = f"""
        FROM python:3.11-slim
        WORKDIR /app

        COPY pyproject.toml poetry.lock ./
        RUN pip install poetry && \
        poetry config virtualenvs.create false && \
        poetry install --no-interaction --no-ansi

        COPY . .

        EXPOSE {PORT}

        CMD ["python3", "{file_name}.py"]"""

        with open(f"./tmp/{file_name}.dockerfile", "w") as file:
            file.write(dockerfile)

        image, build_logs = client.images.build(
            path=".",
            dockerfile=f"./tmp/{file_name}.dockerfile",
            cache_from=[],
            tag={agent_name},
            buildargs=None,
            rm=True,
            forcerm=True,
        )

        spec = {}
        spec["name"] = agent_name
        spec["type"] = "AGENT"
        spec["image"] = agent_name
        spec["ports"] = PORT
        spec["envars"] = envars
        agent_specs.append(spec)
    return agent_specs


def build_tool_images():
    client = docker.from_env()

    with open("blacksmith.yaml", "r") as f:
        data = yaml.safe_load(f)

    tools = data["tools"]
    tool_specs = []

    for tool in tools:
        file_name = tool["handler"]
        tool_name = tool["name"].lower()  # this needs to be lowercase or k8s will error...
        envars = tool.get("env", {})
        PORT = tool.get("port", 5000)
        model = tool.get("model", {})
        if model:
            envars.update({"MODEL": model["name"], "TEMPERATURE": model["temperature"]})
        envars.update(
            {
                "TOOL_SERVICE_NAME": f"{tool_name}-tool",  # this should correspond to the service name that exposes this tool
                "PORT": PORT,
            }
        )
        dockerfile = f"""
        FROM python:3.11-slim
        WORKDIR /app

        COPY pyproject.toml poetry.lock ./
        RUN pip install poetry && \
        poetry config virtualenvs.create false && \
        poetry install --no-interaction --no-ansi

        COPY . .

        EXPOSE {PORT}

        CMD ["python3", "{file_name}.py", "--tool={tool["name"]}"]"""

        with open(f"./tmp/{file_name}.dockerfile", "w") as file:
            file.write(dockerfile)

        image, build_logs = client.images.build(
            path=".",
            dockerfile=f"./tmp/{file_name}.dockerfile",
            tag={tool_name},
            buildargs=None,
            rm=True,
            forcerm=True,
        )

        spec = {}
        spec["name"] = tool_name
        spec["type"] = "TOOL"
        spec["image"] = tool_name
        spec["ports"] = PORT
        spec["envars"] = envars

        tool_specs.append(spec)
    return tool_specs
