import time
import argparse
import os
import shutil
from blacksmith.scripts.images import build_agent_images, build_tool_images
from blacksmith.scripts.k8s import (
    create_k8s_manifest,
    create_redis,
    apply_k8s_manifest,
    apply_redis,
    remove,
)
from blacksmith.scripts.run import run_container, create_network, start_tool_registry, ping_registry


def run_command(args):
    # Create temporary build path
    os.makedirs("./tmp")

    print("🐳 Building agent images...")
    agent_specs = build_agent_images()
    print("✨ Completed!")
    print("🐳 Building tool images...")
    tool_specs = build_tool_images()
    print("✨ Completed!")

    # Remove intermediate build files
    shutil.rmtree("./tmp")

    # Create container networking
    create_network()

    # Create the tool registry container
    print("🧰 Spinning up tool registry...")
    start_tool_registry()

    # Block on health check
    ping_registry()

    # Create agent containers
    print("👷 Creating agent containers...")
    for agent_spec in agent_specs:
        environment = agent_spec["envars"]
        port = environment["PORT"]
        run_container(
            image_name=agent_spec["image"],
            container_name=agent_spec["name"],
            ports={f"{port}/tcp": port},
            environment=agent_spec["envars"],
        )
    print("✨ Completed!")

    # Create tool containers
    print("🔧 Creating tool containers...")
    for tool_spec in tool_specs:
        run_container(
            image_name=tool_spec["image"],
            container_name=f"{tool_spec['name']}-tool",  # container name has to match this format: '{tool name define in YAML}-tool'
            ports=None,
            environment=tool_spec["envars"],
        )
    print("✨ Completed!")


def build_command(args):
    # Create temporary build path
    os.makedirs("./tmp")

    print("🕵️‍♀️  Building agent images...")
    agent_specs = build_agent_images()
    print("✨ Completed!")
    print("🛠️  Building tool images...")
    tool_specs = build_tool_images()
    print("✨ Completed!")

    # Remove intermediate build files
    shutil.rmtree("./tmp")

    # Create k8s manifests
    os.makedirs("./k8s")

    # Clear existing manifest.yaml file
    with open(f"./k8s/manifest.yaml", "w") as file:
        file.write("")

    print("📦 Creating manifest...")
    create_k8s_manifest(agent_specs, tool_specs)
    print("✨ Completed!")

    # Build dependency containers
    print("⚙️  Building dependencies...")
    create_redis()
    print("✨ Completed!")


def apply_command(args):
    print("🚀 Deploying Redis tool registry...")
    apply_redis()
    print("✨ Deployment completed!")
    print("🚀 Deploying agent and tools...")
    time.sleep(2)  # use a liveness probe here instead
    apply_k8s_manifest()
    print("✨ Deployment completed!")


def delete_command(args):
    print("🚫 Deleting deployments...")
    remove()
    print("✅ Deployments deleted.")

    # Remove k8s when done
    shutil.rmtree("./k8s")


def main():
    parser = argparse.ArgumentParser(prog="blacksmith")
    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    # Build step (images, manifest files)
    build_parser = subparsers.add_parser("build", help="Build tools")
    build_parser.set_defaults(func=build_command)

    # Run step (build images and run as standalone containers)
    build_parser = subparsers.add_parser("run", help="Run")
    build_parser.set_defaults(func=run_command)

    # Apply step (kubectl apply)
    build_parser = subparsers.add_parser("apply", help="Apply")
    build_parser.set_defaults(func=apply_command)

    # Remove all deployments
    build_parser = subparsers.add_parser("delete", help="Remove all deployments")
    build_parser.set_defaults(func=delete_command)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
