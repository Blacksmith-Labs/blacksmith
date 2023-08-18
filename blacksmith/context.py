from contextlib import contextmanager
import os
from pydantic import BaseModel
from typing import Any, Optional


@contextmanager
def model(model: str, temperature: int):
    envars = os.environ.copy()
    try:
        os.environ.update({"MODEL": model, "TEMPERATURE": str(temperature)})
        yield
    finally:
        # Restore the original environment variables
        os.environ.clear()
        os.environ.update(envars)


class Config(BaseModel):
    """
    Configuration class for LLM calls.

    Attributes:
        model (Optional[str]): The name of the LLM model to use.
        temperature (Optional[float]): The temperature to use for LLM sampling.
        api_key (Optional[str]): The API key to use for OpenAI authentication.

    Usage:
    ```
        cfg = Config(
          model="gpt-4-0613",
          temperature=0.1,
          api_key="sk-XXXXXXXXXXXXXXXXXXXXXXXX"
        )
    ```
    """

    model: Optional[str] = os.getenv("MODEL")
    temperature: Optional[float] = os.getenv("TEMPERATURE")
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    def model_post_init(self, __context: Any) -> None:
        if self.model:
            os.environ["MODEL"] = self.model
        if self.temperature:
            os.environ["TEMPERATURE"] = str(self.temperature)
        if self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key

    def load(self):
        """
        Loads the default configuration from environment variables.
        """
        try:
            self.model = os.getenv("MODEL")
            self.temperature = float(os.getenv("TEMPERATURE"))
            self.api_key = os.getenv("OPENAI_API_KEY")
        except Exception as e:
            raise KeyError(
                f"Failed to load default configuration. Please check that the Config object has been initialized. Error: {e}"
            )
