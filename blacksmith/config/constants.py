from enum import Enum

OPEN_SOURCE_MODELS = [
    "llama-2-7b",
    "llama-2-7b-chat",
    "llama-2-13b",
    "llama-2-13b-chat",
    "llama-7b",
    "falcon-7b",
    "falcon-7b-instruct",
    "falcon-40b",
    "falcon-40b-instruct",
    "mpt-7b",
    "mpt-7b-instruct",
    "flan-t5-xxl",
]

DOCKER_NETWORK_NAME = "agent-network"

REGISTRY_HEALTH_CHECK_RETRIES = 3

REGISTRY_HEALTH_CHECK_LIMIT = 2

REGISTRY_HEALTH_CHECK_BACKOFF = 1

REGISTRY_CONTAINER_NAME = "tool-registry"

# TODO: Update this to support more types
TOOL_TYPE_MAPPINGS = {"str": "string", "int": "integer"}


class ChatRoles(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
