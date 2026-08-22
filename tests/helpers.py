import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tracker.config.settings import Settings  # noqa: E402
from tracker.core.models import Projects, new_project  # noqa: E402


def make_settings(**overrides) -> Settings:
	settings = Settings.merged({})

	for key, value in overrides.items():
		settings = settings.override(key.replace("__", "."), value)

	return settings


def make_projects(*entries: tuple[str, str, str, str]) -> Projects:
	projects: Projects = {}

	for index, (path, status, last_touched, note) in enumerate(entries, 1):
		projects[path] = new_project(
			path,
			status=status,
			last_touched=last_touched,
			note=note,
			project_id=index,
		)

	return projects


SAMPLE = (
	("/home/user/code/alpha", "current", "2026-01-05 10:00:00", "short note"),
	("/home/user/code/beta", "archived", "2026-02-10 10:00:00", ""),
	("/home/user/code/gamma", "todo", "2025-12-01 10:00:00", "a much longer note " * 4),
)
