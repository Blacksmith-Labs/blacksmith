from contextlib import contextmanager
import os
from pydantic import BaseModel
from blacksmith.utils.tokenizer import get_encodings
from typing import Any, Optional, Callable


@contextmanager
def model(model: str, temperature: int):
    envars = os.environ.copy()
    try:
        os.environ.update(
            {"MODEL": model, "TEMPERATURE": str(temperature), "USING_CONTEXT": "true"}
        )
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
        on_completion (Optional[list[Callabe]]): Functions called after a successful completion.

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
    on_completion: Optional[list[Callable]] = []
    bias: Optional[dict] = {}

    def model_post_init(self, __context: Any) -> None:
        if self.model and not os.environ.get("MODEL"):
            os.environ["MODEL"] = self.model
        if self.temperature and not os.environ.get("TEMPERATURE"):
            os.environ["TEMPERATURE"] = str(self.temperature)
        if self.api_key and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = self.api_key

    def load(self) -> "Config":
        """
        Loads the default configuration from environment variables.

        This method can only be called after a Config object has been previously initialized.
        """
        try:
            self.model = os.getenv("MODEL")
            self.temperature = float(os.getenv("TEMPERATURE"))
            self.api_key = os.getenv("OPENAI_API_KEY")
            return self
        except Exception as e:
            raise RuntimeError(
                f"Failed to load default configuration. Please check that the Config object has been initialized. Error: {e}"
            )

    def update_bias(self, token: str, value: int) -> None:
        """
        Updates the bias for `token`.
        """
        encodings = get_encodings(model=self.model, token=token)
        for token in encodings:
            self.bias.update({token: value})
