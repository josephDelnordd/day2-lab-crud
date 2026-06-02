import json
import logging
from pathlib import Path
from typing import List
from models import Server

logger = logging.getLogger(__name__)


class ConfigError(ValueError):
    """Raised when configuration loading fails."""
    pass


class ConfigLoader:
    """Loads server configuration from a JSON file."""

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> List[Server]:
        logger.info("Loading config from %s", self.path)

        try:
            raw = json.loads(self.path.read_text())
        except FileNotFoundError as exc:
            raise ConfigError(f"Config file not found: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON: {exc}") from exc

        servers = []
        for idx, entry in enumerate(raw, start=1):
            servers.append(
                Server(
                    id=idx,
                    name=entry["name"],
                    host=entry["host"],
                    port=entry["port"],
                    tags=entry.get("tags", []),
                )
            )

        logger.info("Loaded %d servers", len(servers))
        return servers