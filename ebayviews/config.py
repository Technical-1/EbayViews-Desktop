from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".ebayviews"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    concurrency: int = 5
    interval_seconds: float = 0.25
    timeout_seconds: float = 10.0
    retries: int = 2
    max_seller_pages: int = 5
    rotate_user_agents: bool = True
    proxy_file: str = ""

    def validate(self) -> "AppConfig":
        self.concurrency = min(max(int(self.concurrency), 1), 25)
        self.interval_seconds = max(float(self.interval_seconds), 0.0)
        self.timeout_seconds = max(float(self.timeout_seconds), 1.0)
        self.retries = min(max(int(self.retries), 0), 10)
        self.max_seller_pages = min(max(int(self.max_seller_pages), 1), 25)
        self.rotate_user_agents = bool(self.rotate_user_agents)
        self.proxy_file = str(self.proxy_file or "")
        return self

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        values = {key: value for key, value in data.items() if key in allowed}
        return cls(**values).validate()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self.validate())


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if not path.exists():
        return AppConfig()
    try:
        return AppConfig.from_dict(json.loads(path.read_text()))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return AppConfig()


def save_config(config: AppConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config.to_dict(), indent=2) + "\n")


def load_proxies(proxy_file: str) -> list[str]:
    if not proxy_file:
        return []
    path = Path(proxy_file).expanduser()
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
