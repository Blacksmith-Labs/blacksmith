import os

MODEL = os.getenv("MODEL")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0))

IS_USING_CONTEXT = lambda: os.environ.get("USING_CONTEXT") == "true"
