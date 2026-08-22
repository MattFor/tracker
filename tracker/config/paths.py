import os

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent

MAN_DIR = PROJECT_ROOT / "man"
HELP_FILE = MAN_DIR / "help.txt"

DEFAULT_SETTINGS_FILE = PROJECT_ROOT / "settings.toml"
USER_SETTINGS_FILE = PROJECT_ROOT / "my_settings.toml"

DEFAULT_DATA_FILE = "data.pkl"


def settings_file() -> Path:
	override = os.environ.get("TRACKER_SETTINGS")

	if override:
		return resolve(override)

	if USER_SETTINGS_FILE.exists():
		return USER_SETTINGS_FILE

	return DEFAULT_SETTINGS_FILE


def resolve(path: str | os.PathLike[str]) -> Path:
	resolved = Path(os.path.expanduser(str(path)))

	if not resolved.is_absolute():
		resolved = PROJECT_ROOT / resolved

	return resolved


def data_file(configured: str | None = None) -> Path:
	return resolve(os.environ.get("TRACKER_DATA") or configured or DEFAULT_DATA_FILE)


def state_dir() -> Path:
	base = os.environ.get("XDG_STATE_HOME")

	if base:
		return Path(base) / "tracker"

	return Path.home() / ".local" / "state" / "tracker"


def daemon_pid_file() -> Path:
	return state_dir() / "daemon.pid"


def daemon_log_file() -> Path:
	return state_dir() / "daemon.log"
