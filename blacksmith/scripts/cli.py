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

    print("📦  Creating manifest...")
    create_k8s_manifest(agent_specs, tool_specs)
    print("✨ Completed!")
    print("⚙️  Building Redis tool registry...")
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
