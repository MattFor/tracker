import os
import copy
import tomllib
import subprocess

from pathlib import Path
from typing import Any, Iterator

from tracker.config import paths
from tracker.util.files import read_toml
from tracker.util.unknown import Unknown
from tracker.config.defaults import CHOICES, OPEN_TABLES, defaults


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
	merged = dict(base)

	for key, value in override.items():
		current = merged.get(key)

		if isinstance(current, dict) and isinstance(value, dict):
			merged[key] = _merge(current, value)
		else:
			merged[key] = value

	return merged


def _flatten(data: dict[str, Any], prefix: str = "") -> Iterator[tuple[str, Any]]:
	for key, value in data.items():
		path = f"{prefix}.{key}" if prefix else key

		if isinstance(value, dict) and path not in OPEN_TABLES:
			yield from _flatten(value, path)
		else:
			yield path, value


class Settings:
	def __init__(
		self,
		data: dict[str, Any] | None = None,
		*,
		path: Path | None = None,
		problems: list[str] | None = None,
	) -> None:
		self._problems: list[str] = list(problems or [])

		if data is not None:
			self._data = data
			self._path = path or paths.settings_file()
			return

		self._path = path or paths.settings_file()

		loaded, error = read_toml(self._path)

		if error:
			# Keep running on the defaults rather than dying on a typo
			self._problems.append(error)
			loaded = None

		elif loaded is None:
			self._problems.append(f"{self._path.name} was not found, using defaults")

		self._data = _merge(defaults(), loaded or {})

		self._problems.extend(self._unknown_keys(loaded or {}))

	@classmethod
	def merged(
		cls, data: dict[str, Any] | None, *, path: Path | None = None
	) -> "Settings":
		data = data or {}

		return cls(
			_merge(defaults(), data),
			path=path,
			problems=cls._unknown_keys(data),
		)

	#
	# Introspection
	#

	@staticmethod
	def _unknown_keys(loaded: dict[str, Any]) -> list[str]:
		known = {key for key, _ in _flatten(defaults())}

		return [
			f"unknown setting '{key}' in the configuration"
			for key, _ in _flatten(loaded)
			if key not in known
		]

	@property
	def path(self) -> Path:
		return self._path

	@property
	def raw(self) -> dict[str, Any]:
		return self._data

	@property
	def problems(self) -> list[str]:
		return list(self._problems)

	def items(self) -> Iterator[tuple[str, Any]]:
		yield from _flatten(self._data)

	#
	# Reading
	#

	def __getitem__(self, key: str) -> Any:
		value = self._data.get(key)

		if isinstance(value, dict):
			return Settings(value, path=self._path)

		if value is None:
			return Unknown()

		return value

	def __contains__(self, key: str) -> bool:
		return key in self._data

	def get(self, path: str, default: Any = None) -> Any:
		current: Any = self._data

		for key in path.split("."):
			if not isinstance(current, dict) or key not in current:
				return default

			current = current[key]

		return current

	#
	# Writing
	#

	def override(self, path: str, value: Any) -> "Settings":
		keys = path.split(".")

		expected = self.get(path, Unknown())

		if isinstance(expected, Unknown):
			raise KeyError(path)

		value = coerce(path, value, expected)

		data = copy.deepcopy(self._data)
		current = data

		for key in keys[:-1]:
			if not isinstance(current.get(key), dict):
				raise KeyError(path)

			current = current[key]

		current[keys[-1]] = value

		return Settings(data, path=self._path, problems=self._problems)

	def edit(self) -> None:
		editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")

		command = [editor, str(self.path)] if editor else ["xdg-open", str(self.path)]

		try:
			subprocess.run(command, check=False)
		except (OSError, subprocess.SubprocessError) as error:
			print(f"[ERROR] could not open an editor: {error}")
			print(f"the settings file is at {self.path}")


#
# Values
#


def parse_setting_value(value: str) -> Any:
	try:
		return tomllib.loads(f"value = {value}")["value"]
	except tomllib.TOMLDecodeError:
		return value


def coerce(path: str, value: Any, expected: Any) -> Any:
	choices = CHOICES.get(path)

	if choices is not None:
		text = str(value).strip().lower()

		if text not in choices:
			raise ValueError(f"'{path}' must be one of: {', '.join(choices)}")

		return text

	if isinstance(expected, bool):
		if isinstance(value, bool):
			return value

		text = str(value).strip().lower()

		if text in ("true", "yes", "on", "1"):
			return True

		if text in ("false", "no", "off", "0"):
			return False

		raise ValueError(f"'{path}' must be true or false")

	if isinstance(expected, int) and not isinstance(value, bool):
		try:
			return int(value)
		except (TypeError, ValueError):
			raise ValueError(f"'{path}' must be a whole number") from None

	if isinstance(expected, list):
		if isinstance(value, list):
			return value

		if isinstance(value, str):
			# Allow `columns=id,name` as a shortcut for a TOML array
			return [item.strip() for item in value.split(",") if item.strip()]

		raise ValueError(f"'{path}' must be a list")

	if isinstance(expected, dict):
		if isinstance(value, dict):
			return value

		raise ValueError(f"'{path}' must be a table")

	if isinstance(expected, str):
		return str(value)

	return value


settings = Settings()
