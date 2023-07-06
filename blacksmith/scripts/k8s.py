import yaml
import subprocess


def create_k8s_manifest(agent_specs, tool_specs):
    for spec in agent_specs + tool_specs:
        try:
            # Generate a deployment for the tool
            deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": f"{spec['name']}-deployment", "labels": {"app": spec["name"]}},
                "spec": {
                    "replicas": 1,
                    "selector": {"matchLabels": {"app": spec["name"], "tier": spec["type"]}},
                    "template": {
                        "metadata": {
                            "labels": {
                                "app": spec["name"],
                                "tier": spec["type"],
                            }
                        },
                        "spec": {
                            "containers": [
                                {
                                    "name": f"{spec['name']}-container",
                                    "image": f"{spec['image']}:latest",
                                    "imagePullPolicy": "Never",
                                    "env": [
                                        {"name": envar[0], "value": str(envar[1])}
                                        for envar in spec["envars"].items()
                                    ],
                                }
                            ]
                        },
                    },
                },
            }
            # Add the deployment to the manifest
            with open(f"./k8s/manifest.yaml", "a") as file:
                file.write(yaml.dump(deployment))
                file.write("---\n")

            if spec["type"] == "AGENT":
                # Build the NodePort service
                node_port = {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {"name": f"{spec['name']}-service"},
                    "spec": {
                        "type": "NodePort",
                        "selector": {"app": spec["name"], "tier": spec["type"]},
                        "ports": [
                            {
                                "name": "http",
                                "port": 80,
                                "targetPort": spec["ports"],
                                "nodePort": 30000,
                            }
                        ],
                    },
                }
                with open(f"./k8s/manifest.yaml", "a") as file:
                    file.write(yaml.dump(node_port))
                    file.write("---\n")

            if spec["type"] == "TOOL":
                # Generate a service for the deployment
                service = {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {"name": f"{spec['name']}-tool"},
                    "spec": {
                        "selector": {"app": spec["name"], "tier": spec["type"]},
                        "ports": [
                            {
                                "name": "http",
                                "protocol": "TCP",
                                "port": 80,
                                "targetPort": spec["ports"],
                            }
                        ],
                    },
                }
                with open(f"./k8s/manifest.yaml", "a") as file:
                    file.write(yaml.dump(service))
                    file.write("---\n")
        except Exception as e:
            print(f"Error: could not build {spec}: {e}")


def create_redis():
    # Add the deployment to the manifest
    redis_deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "redis-deployment"},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": "redis"}},
            "template": {
                "metadata": {"labels": {"app": "redis"}},
                "spec": {
                    "containers": [
                        {
                            "name": "redis",
                            "image": "redis:latest",
                            "ports": [{"containerPort": 6379}],
                        }
                    ]
                },
            },
        },
    }
    with open(f"./k8s/redis.yaml", "w") as file:
        file.write("# REDIS DEPLOYMENT # \n")
        file.write(yaml.dump(redis_deployment))

    # Add the service to the manifest
    redis_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "redis-service"},
        "spec": {
            "selector": {"app": "redis"},
            "ports": [{"name": "redis", "port": 6379}],
        },
    }
    with open(f"./k8s/redis.yaml", "a") as file:
        file.write("---\n")
        file.write(yaml.dump(redis_service))


def apply_redis():
    subprocess.run(["kubectl", "apply", "-f", "./k8s/redis.yaml"], check=True)


def apply_k8s_manifest():
    subprocess.run(["kubectl", "apply", "-f", "./k8s/manifest.yaml"], check=True)


def remove():
    subprocess.run(["kubectl", "delete", "-f", "./k8s/redis.yaml"], check=True)
    subprocess.run(["kubectl", "delete", "-f", "./k8s/manifest.yaml"], check=True)
