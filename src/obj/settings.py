import os
import subprocess

from typing import Any
from pathlib import Path

from src.ansi import *

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
				"list_limit": 10,
				"show_headers": True,
				"show_notes": True,
				"columns": ["tid", "id", "name", "status", "last_touched"],
				"time_format": "%Y-%m-%d %H:%M:%S",
			},
			"sorting": {
				# name / path / status / time / id / tid
				"by": "time",
				# ascending / descending
				"direction": "descending",
			},
			"projects": {
				# Status assigned to newly discovered projects
				"default_status": "unknown",
				# Directories ignored during project discovery
				"ignore": [
					".git",
					".venv",
					"venv",
					"node_modules",
					"target",
					"dist",
					"build",
					"__pycache__",
				],
			},
			"scan": {
				# Detect projects by the presence of .git
				"detect_git": True,
				# Search recursively through subdirectories
				"recursive": True,
				# Stop searching inside a project once it is detected
				"stop_at_project": True,
			},
			"output": {"colour": True, "compact": False, "absolute_paths": True},
			"database": {"file": "data.pkl"},
			"logging": {"always_verbose": False},
		}

	@property
	def path(self) -> Path:
		return _CONFIG_PATH

	def display(self) -> None:
		sections = {
			"display": "Display",
			"sorting": "Sorting",
			"projects": "Projects",
			"scan": "Scanning",
			"output": "Output",
			"database": "Database",
			"logging": "Logging",
		}

		print(f"{BOLD}{CYAN}Tracker Settings{RESET}")
		print(f"{GRAY}{'─' * 70}{RESET}")

		first: bool = True

		for section, title in sections.items():
			data = self._data.get(section)

			if not isinstance(data, dict):
				continue

			print(f"{"\n" if not first else ""}{BOLD}{title}{RESET}")

			first = False

			for key, value in data.items():
				label = key.replace("_", " ").title()

				if isinstance(value, list):
					value = ", ".join(str(item) for item in value)

				print(f"  {label:<18} {YELLOW}{value}{RESET}")

	# noinspection shadowing-names
	def edit(self) -> None:
		editor = os.environ.get("EDITOR")

		if editor:
			subprocess.run([editor, str(self.path)])
			return

		subprocess.run(["xdg-open", str(self.path)])


settings = Settings()
