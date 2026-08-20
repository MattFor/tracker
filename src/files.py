import json
import pickle
import tomllib

from typing import Any
from pathlib import Path


#
# Json
#


def save_json(path: Path, data: dict[str, Any]) -> bool:
	try:
		with open(path, "w") as f:
			json.dump(data, f, indent=4)
		return True
	except OSError:
		return False


def load_json(path: Path) -> dict[str, Any] | False:
	try:
		with open(path, "r") as f:
			return json.load(f)
	except (FileNotFoundError, json.JSONDecodeError):
		return False


#
# TOML
#


def load_toml(path: Path) -> dict[str, Any] | False:
	try:
		with open(path, "rb") as f:
			return tomllib.load(f)
	except (FileNotFoundError, tomllib.TOMLDecodeError):
		return False


#
# Pickle
#


def save_pkl(path: Path, data: Any) -> bool:
	try:
		with open(path, "wb") as f:
			pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
		return True
	except OSError:
		return False


def load_pkl(path: Path) -> Any | None:
	try:
		with open(path, "rb") as f:
			return pickle.load(f)
	except (FileNotFoundError, pickle.UnpicklingError):
		return False
