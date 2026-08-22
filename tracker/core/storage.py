import time

from pathlib import Path

from tracker.config import paths
from tracker.util.files import load_pkl, save_pkl
from tracker.core.models import Projects, normalise
from tracker.config.settings import Settings, settings as default_settings


def data_path(settings: Settings | None = None) -> Path:
	settings = settings or default_settings

	return paths.data_file(settings.get("database.file"))


def load_data(settings: Settings | None = None) -> Projects:
	path = data_path(settings)

	data, error = load_pkl(path)

	if error is not None:
		backup = path.with_name(f"{path.name}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}")

		print(f"[ERROR] the database could not be read ({error})")

		try:
			path.replace(backup)
			print(f"the unreadable file was kept as {backup}")
		except OSError:
			pass

		return {}

	if data is None:
		return {}

	return normalise(data)


def save_data(data: Projects, settings: Settings | None = None) -> bool:
	path = data_path(settings)

	# Don't persist the... "temporary" ID
	for project in data.values():
		project.pop("tid", None)

	if not save_pkl(path, data):
		print(f"[ERROR] could not write the database at {path}")
		return False

	return True


def create_data(settings: Settings | None = None) -> bool:
	return save_data({}, settings)
