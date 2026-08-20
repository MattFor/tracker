from typing import Any
from pathlib import Path

from src.utils import Unknown
from src.files import load_toml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


class Settings:
	def __init__(self, data: dict[str, Any] | None = None) -> None:
		if data is not None:
			self._data = data
			return

		data = load_toml(_CONFIG_PATH)

		self._data = data if data is not False else {}

	def __getitem__(self, key: str) -> Any:
		value = self._data.get(key)

		if isinstance(value, dict):
			return Settings(value)

		if value is None:
			return Unknown()

		return value


settings = Settings()
