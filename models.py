from dataclasses import dataclass, field
from typing import List
from pydantic import BaseModel, Field


@dataclass
class Server:
    """Internal server representation."""
    id: int
    name: str
    host: str
    port: int
    status: str = "unknown"
    tags: List[str] = field(default_factory=list)

    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    """Schema for registering a new server."""
    name: str
    host: str
    port: int = Field(default=8080, ge=1, le=65535)
    tags: List[str] = []


class ServerOut(BaseModel):
    """Schema returned to the API client."""
    id: int
    name: str
    host: str
    port: int
    status: str
    tags: List[str] = []

    model_config = {"from_attributes": True}