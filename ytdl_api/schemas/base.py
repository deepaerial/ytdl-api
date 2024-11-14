import humps
from pydantic import BaseModel, ConfigDict


class BaseModel_(BaseModel):
    """Base class for all schemas."""
    model_config = ConfigDict(alias_generator=humps.camelize, populate_by_name=True)
