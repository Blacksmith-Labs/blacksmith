import docker
from blacksmith.config.constants import DOCKER_NETWORK_NAME


def create_network():
    client = docker.from_env()
    try:
        client.networks.create(name=DOCKER_NETWORK_NAME)
    except Exception as e:
        return e


def run_container(image_name, container_name, ports, environment):
    client = docker.from_env()
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
