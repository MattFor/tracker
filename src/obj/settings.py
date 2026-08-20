from typing import Any
from pathlib import Path

from src.utils import Unknown
from src.files import load_toml

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "settings.toml"


class Settings:
	def __init__(self, data: dict[str, Any] | None = None) -> None:
		if data is not None:
			self._data = data
			return

		data = load_toml(_CONFIG_PATH)

		if data is False:
			print("[ERROR] could not load settings, using default")
			self._data = self._default()
		else:
			self._data = data

	def __getitem__(self, key: str) -> Any:
		value = self._data.get(key)

		if isinstance(value, dict):
			return Settings(value)

		if value is None:
			return Unknown()

		return value

	@staticmethod
	def _default() -> dict[str, Any]:
		return {
			"display": {
				"list_limit": 5,
				"show_headers": False,
				"columns": ["name", "status", "last_touched"],
				"time_format": "%Y-%m-%d %H:%M:%S",
			},
			"sorting": {"by": "name", "direction": "ascending"},
			"projects": {
				"default_status": "unknown",
				"ignore": [".git", ".venv", "node_modules", "target", "dist", "build"],
			},
			"scan": {"detect_git": True, "recursive": True, "stop_at_project": True},
			"output": {"colour": True, "compact": False, "absolute_paths": True},
			"database": {"file": "data.pkl"},
			"logging": {"always_verbose": False},
		}


settings = Settings()
