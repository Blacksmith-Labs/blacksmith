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
        self.model = os.getenv("MODEL")
        self.temperature = float(os.getenv("TEMPERATURE"))
        self.api_key = os.getenv("OPENAI_API_KEY")
