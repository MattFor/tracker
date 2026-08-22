from typing import Any

from tracker.util.files import load_toml
from tracker.util.unknown import Unknown
from tracker.config.paths import PROJECT_ROOT


class PyProject:
	def __init__(self, data: dict[str, Any] | None = None) -> None:
		if data is not None:
			self._data = data
			return

		self._data = load_toml(PROJECT_ROOT / "pyproject.toml") or {}

	def __getitem__(self, key: str) -> Any:
		if key in self._data:
			value = self._data[key]

		elif isinstance(self._data.get("project"), dict) and key in self._data["project"]:
			value = self._data["project"][key]

		else:
			return Unknown()

		if isinstance(value, dict):
			return PyProject(value)

		return value

	def __contains__(self, key: str) -> bool:
		return not isinstance(self[key], Unknown)

	@property
	def version(self) -> str:
		return str(self["version"])

	@property
	def name(self) -> str:
		return str(self["name"])

	@property
	def author(self) -> str:
		authors = self["authors"]

		if isinstance(authors, list) and authors:
			first = authors[0]

			if isinstance(first, dict):
				return str(first.get("name", "unknown"))

			return str(first)

		return "unknown"


project = PyProject()
