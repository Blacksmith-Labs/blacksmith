import docker


NETWORK_NAME = "agent-network"


def create_network():
    client = docker.from_env()
    try:
        client.networks.create(NETWORK_NAME, driver="bridge")
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
            network=NETWORK_NAME,
            detach=True,
        )
    except Exception as e:
        return e
