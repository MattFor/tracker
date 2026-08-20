import json
import pickle
import tomllib

from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def save_settings(settings: dict[str, Any]) -> None:
	with open(_PROJECT_ROOT / "settings.json", "w") as f:
		json.dump(settings, f, indent=4)


def load_settings() -> dict[str, Any] | False:
	try:
		with open(_PROJECT_ROOT / "settings.json", "r") as f:
			settings: dict[str, Any] = json.load(f)
		return settings
	except FileNotFoundError:
		return False


def save_data(data: dict[str, Any]) -> None:
	with open(_PROJECT_ROOT / "data.pkl", "wb") as f:
		pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_data() -> dict[str, Any] | False:
	try:
		with open(_PROJECT_ROOT / "data.pkl", "rb") as f:
			data: dict[str, Any] = pickle.load(f)
		return data
	except FileNotFoundError:
		return False


def load_pyproject_toml() -> dict[str, Any] | False:
	try:
		with open(_PROJECT_ROOT / "pyproject.toml", "rb") as f:
			pyproj: dict[str, Any] = tomllib.load(f)
		return pyproj
	except FileNotFoundError:
		return False


def create_settings() -> bool:
	try:
		with open(_PROJECT_ROOT / "settings.json", "w") as f:
			json.dump({}, f, indent=4)
		return True
	except FileNotFoundError:
		return False


def create_data() -> bool:
	try:
		with open(_PROJECT_ROOT / "data.pkl", "wb") as f:
			pickle.dump({}, f, protocol=pickle.HIGHEST_PROTOCOL)
		return True
	except FileNotFoundError:
		return False
