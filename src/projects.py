from typing import NotRequired, TypedDict

from src.utils import *
from src.obj.settings import Settings


class Project(TypedDict):
	path: str
	status: str
	last_touched: str
	note: NotRequired[str]


Projects = dict[str, Project]


def print_projects(projects: Projects, settings: Settings) -> None:
	if not projects:
		print("no projects found")
		return

	headers = {
		"name": "NAME",
		"path": "PATH",
		"status": "STATUS",
		"last_touched": "LAST TOUCHED",
	}

	columns: list[str] = settings["display"]["columns"]
	list_limit: int = settings["display"]["list_limit"]
	show_headers: bool = settings["display"]["show_headers"]
	show_notes: bool = settings["display"]["show_notes"]
	compact: bool = settings["output"]["compact"]
	absolute_paths: bool = settings["output"]["absolute_paths"]

	columns = [column for column in columns if column in headers]

	if not columns:
		print("no valid columns configured")
		return

	sort_by: str = settings["sorting"]["by"]
	sort_direction: str = settings["sorting"]["direction"]

	if sort_by not in headers:
		sort_by = "name"

	reverse: bool = sort_direction == "descending"

	def sort_key(item: tuple[str, Project]) -> str:
		# noinspection shadowing-names
		path, project = item

		if sort_by == "name":
			return Path(path).name.lower()

		if sort_by == "path":
			return path.lower()

		return project[sort_by].lower()

	sorted_projects = sorted(projects.items(), key=sort_key, reverse=reverse)

	selected_projects = sorted_projects[:list_limit]

	rows = []

	for path, project in selected_projects:
		row = []

		for column in columns:
			if column == "name":
				value = Path(path).name

			elif column == "path":
				value = path

				if not absolute_paths:
					value = os.path.relpath(path)

			else:
				value = project[column]

			row.append(value)

		rows.append((path, project, row))

	widths = [
		max(
			len(headers[column]),
			*(len(row[i]) for _, _, row in rows),
		)
		for i, column in enumerate(columns)
	]

	spacing = " " if compact else "  "

	if show_headers:
		header = spacing.join(
			headers[column].ljust(widths[i]) for i, column in enumerate(columns)
		)

		separator = spacing.join("-" * width for width in widths)

		print(header)
		print(separator)

	for path, project, row in rows:
		print(spacing.join(value.ljust(widths[i]) for i, value in enumerate(row)))

		note = project.get("note", "")

		if show_notes and note:
			print(f"    {GRAY}{note}{RESET}")


def find_projects(path: str, settings: Settings) -> Projects:
	projects: Projects = {}

	root_path = Path(path).expanduser().resolve()

	if not root_path.exists() or not root_path.is_dir():
		return projects

	recursive: bool = settings["scan"]["recursive"]
	detect_git: bool = settings["scan"]["detect_git"]
	ignore: list[str] = settings["projects"]["ignore"]
	time_format: str = settings["display"]["time_format"]
	stop_at_project: bool = settings["scan"]["stop_at_project"]
	default_status: str = settings["projects"]["default_status"]

	for current_root, dirs, _ in os.walk(root_path):
		current_path = Path(current_root)
		git_dir = current_path / ".git"

		dirs[:] = [directory for directory in dirs if directory not in ignore]

		is_project = detect_git and (git_dir.is_dir() or git_dir.is_file())

		if is_project:
			last_touched = get_last_touched_date(str(current_path))
			project_path = str(current_path)

			projects[project_path] = {
				"path": project_path,
				"status": default_status,
				"last_touched": (
					last_touched.strftime(time_format)
					if last_touched is not None
					else "unknown"
				),
				"note": "",
			}

			# Don't search already found
			if stop_at_project:
				dirs[:] = []

			continue

		if not recursive:
			dirs[:] = []

	return projects


def get_project(projects: Projects, identifier: str) -> tuple[str, Project] | None:
	identifier = os.path.expanduser(identifier).lower()

	for path, project in projects.items():
		if path.lower() == identifier:
			return path, project

	exact_matches = [
		(path, project)
		for path, project in projects.items()
		if Path(path).name.lower() == identifier
	]

	if len(exact_matches) == 1:
		return exact_matches[0]

	if len(exact_matches) > 1:
		print(f"[ERROR] multiple projects match '{identifier}'")
		return None

	fuzzy_matches = [
		(path, project)
		for path, project in projects.items()
		if Path(path).name.lower().startswith(identifier)
	]

	if len(fuzzy_matches) == 1:
		return fuzzy_matches[0]

	if len(fuzzy_matches) > 1:
		print(f"[ERROR] multiple projects match '{identifier}':")

		for path, _ in fuzzy_matches:
			print(f"  {Path(path).name} | {path}")

		return None

	return None
