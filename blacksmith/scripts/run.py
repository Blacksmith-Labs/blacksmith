import docker
from blacksmith.config.constants import DOCKER_NETWORK_NAME


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
