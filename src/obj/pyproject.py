import tomllib

from typing import Any
from pathlib import Path
from src.utils import Unknown


class PyProj:
	def __init__(self, data: dict[str, Any] | None = None) -> None:
		if data is not None:
			self._data = data
			return

		path = Path(__file__).resolve().parent.parent / "pyproject.toml"

		try:
			with path.open("rb") as f:
				self._data = tomllib.load(f)
		except FileNotFoundError:
			self._data = {}

	def __getitem__(self, key: str) -> Any:
		if key in self._data:
			value = self._data[key]
		elif isinstance(self._data["project"], dict) and key in self._data["project"]:
			value = self._data["project"][key]
		else:
			return Unknown()

		if isinstance(value, dict):
			return PyProj(value)

		return value


project = PyProj()
