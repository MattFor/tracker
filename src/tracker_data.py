from src.files import *

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


#
# Settings
#


def save_settings(settings: dict[str, Any]) -> bool:
	return save_json(_PROJECT_ROOT / "settings.toml", settings)


def load_settings() -> dict[str, Any] | False:
	return load_json(_PROJECT_ROOT / "settings.toml")


def create_settings() -> bool:
	return save_settings({})


#
# Database
#


def save_data(data: dict[str, Any]) -> bool:
	return save_pkl(_PROJECT_ROOT / "data.pkl", data)


def load_data() -> dict[str, Any] | False:
	data = load_pkl(_PROJECT_ROOT / "data.pkl")

	if data is False or not isinstance(data, dict):
		return False

	return data


def create_data() -> bool:
	return save_data({})


#
# Project data
#


def load_pyproject_toml() -> dict[str, Any] | None:
	return load_toml(_PROJECT_ROOT / "pyproject.toml")
