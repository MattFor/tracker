import os

from pathlib import Path
from datetime import datetime
from typing import Callable, Iterable

from tracker.config.settings import Settings
from tracker.core.models import Projects, UNKNOWN_TIME, get_id, new_project


def get_last_touched_date(
	path: str | os.PathLike[str],
	ignore: Iterable[str] = (),
	follow_symlinks: bool = False,
) -> datetime | None:
	root = str(path)

	if not os.path.exists(root):
		return None

	skip = set(ignore)
	latest: float | None = None

	stack: list[str] = [root]
	seen: set[tuple[int, int]] = set()

	while stack:
		current = stack.pop()

		try:
			entries = list(os.scandir(current))
		except OSError:
			continue

		for entry in entries:
			try:
				if entry.is_dir(follow_symlinks=follow_symlinks):
					if entry.name in skip:
						continue

					if follow_symlinks:
						# Guard against symlink loops
						stats = entry.stat()
						key = (stats.st_dev, stats.st_ino)

						if key in seen:
							continue

						seen.add(key)

					stack.append(entry.path)
					continue

				mtime = entry.stat(follow_symlinks=False).st_mtime

			except OSError:
				continue

			if latest is None or mtime > latest:
				latest = mtime

	if latest is None:
		# An empty project still has its own directory timestamp
		try:
			latest = os.stat(root).st_mtime
		except OSError:
			return None

	return datetime.fromtimestamp(latest)


def format_last_touched(moment: datetime | None, time_format: str) -> str:
	if moment is None:
		return UNKNOWN_TIME

	try:
		return moment.strftime(time_format)
	except (ValueError, TypeError):
		return moment.strftime("%Y-%m-%d %H:%M:%S")


def is_project(path: Path, detect_git: bool) -> bool:
	if not detect_git:
		return False

	git = path / ".git"

	return git.is_dir() or git.is_file()


def find_projects(
	path: str | os.PathLike[str],
	settings: Settings,
	projects: Projects | None = None,
	*,
	on_found: Callable[[str, dict], None] | None = None,
) -> Projects:
	if projects is None:
		projects = {}

	root = Path(os.path.expanduser(str(path))).resolve()

	if not root.is_dir():
		return projects

	recursive: bool = settings["scan"]["recursive"]
	detect_git: bool = settings["scan"]["detect_git"]
	stop_at_project: bool = settings["scan"]["stop_at_project"]
	follow_symlinks: bool = settings["scan"]["follow_symlinks"]
	skip_ignored: bool = settings["scan"]["timestamps_skip_ignored"]

	ignore: list[str] = settings["projects"]["ignore"]
	time_format: str = settings["display"]["time_format"]
	default_status: str = settings["projects"]["default_status"]

	timestamp_ignore = ignore if skip_ignored else ()

	for current_root, dirs, _ in os.walk(root, followlinks=follow_symlinks):
		current = Path(current_root)

		dirs[:] = [directory for directory in dirs if directory not in ignore]

		if not recursive and current != root:
			dirs[:] = []

		if not is_project(current, detect_git):
			continue

		project_path = str(current)

		last_touched = format_last_touched(
			get_last_touched_date(project_path, timestamp_ignore, follow_symlinks),
			time_format,
		)

		if project_path in projects:
			projects[project_path]["last_touched"] = last_touched

		else:
			projects[project_path] = new_project(
				project_path,
				status=default_status,
				last_touched=last_touched,
				project_id=get_id(projects),
			)

			if on_found is not None:
				on_found(project_path, projects[project_path])

		if stop_at_project:
			dirs[:] = []

	return projects
