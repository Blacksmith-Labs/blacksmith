import docker
import subprocess
from blacksmith.config.constants import (
    DOCKER_NETWORK_NAME,
    REGISTRY_HEALTH_CHECK_LIMIT,
    REGISTRY_HEALTH_CHECK_RETRIES,
    REGISTRY_HEALTH_CHECK_BACKOFF,
    REGISTRY_CONTAINER_NAME,
)
from tenacity import retry, stop_after_delay, wait_fixed, retry_if_not_result, stop_after_attempt


client = docker.from_env()


def create_network():
    try:
        # Only create the network if one with that name doesn't already exist
        if not any(network.name == DOCKER_NETWORK_NAME for network in client.networks.list()):
            client.networks.create(name=DOCKER_NETWORK_NAME)
    except Exception as e:
        return e


def run_container(image_name, container_name, ports, environment):
    try:
        client.containers.run(
            image=image_name,
            name=container_name,
            ports=ports,
            environment=environment,
            network=DOCKER_NETWORK_NAME,
            detach=True,
        )
    except Exception as e:
        return e


def start_tool_registry():
    run_container(
        image_name="redis:latest",
        container_name=REGISTRY_CONTAINER_NAME,
        ports={"6379/tcp": 6379},
        environment={},
    )


@retry(
    retry=retry_if_not_result(lambda output: output == "PONG"),
    stop=(
        stop_after_delay(REGISTRY_HEALTH_CHECK_LIMIT)
        | stop_after_attempt(REGISTRY_HEALTH_CHECK_RETRIES)
    ),
    wait=wait_fixed(REGISTRY_HEALTH_CHECK_BACKOFF),
)
def ping_registry():
    result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)
    output = result.stdout.strip()
    return output
