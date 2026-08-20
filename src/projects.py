from typing import NotRequired, TypedDict, Any

import re

from src.utils import *
from src.obj.settings import Settings


class Project(TypedDict):
	id: int
	tid: int
	path: str
	status: str
	last_touched: str
	note: NotRequired[str]


Projects = dict[str, Project]


class ListOptions(TypedDict):
	limit: NotRequired[int]
	search: NotRequired[str]
	regex: NotRequired[str]


def get_id(projects: Projects) -> int:
	if not projects:
		return 1

	return max(project["id"] for project in projects.values()) + 1


def _sorted_projects(projects: Projects, settings: Settings) -> list[tuple[str, Project]]:
	sort_by: str = settings["sorting"]["by"]
	sort_direction: str = settings["sorting"]["direction"]

	if sort_by not in ("id", "name", "path", "status", "last_touched", "time"):
		sort_by = "name"

	reverse = sort_direction == "descending"

	def sort_key(item: tuple[str, Project]) -> str:
		# noinspection shadowing-names
		path, project = item

		if sort_by == "id":
			return str(project["id"])

		if sort_by == "name":
			return Path(path).name.lower()

		if sort_by == "path":
			return path.lower()

		if sort_by in ("last_touched", "time"):
			return project["last_touched"]

		return project[sort_by].lower()

	return sorted(
		projects.items(),
		key=sort_key,
		reverse=reverse,
	)


def _get_sorted_projects(projects: Projects, settings: Settings) -> Projects:
	sorted_projects = _sorted_projects(projects, settings)
	result: Projects = {}

	for tid, (path, project) in enumerate(sorted_projects, start=1):
		project["tid"] = tid
		result[path] = project

	return result


def _find_by_number(projects: Projects, number: int) -> list[tuple[str, Project]]:
	matches: list[tuple[str, Project]] = []

	for path, project in projects.items():
		if project["id"] == number or project["tid"] == number:
			matches.append((path, project))

	return matches


def select_projects(
	projects: Projects, settings: Settings, selectors: list[str]
) -> Projects:
	projects = _get_sorted_projects(projects, settings)

	selected: Projects = {}

	def add_project(path: str) -> None:
		selected[path] = projects[path]

	def select_number(number: int) -> None:
		# noinspection shadowing-names
		matches = _find_by_number(projects, number)

		if not matches:
			print(f"[ERROR] no project matches ID/TID '{number}'")
			return

		if len(matches) > 1:
			print(f"[ERROR] ID/TID '{number}' matches multiple projects:")

			for path, project in matches:
				print(f"  ID {project['id']} | TID {project['tid']} | {Path(path).name}")

			return

		add_project(matches[0][0])

	# noinspection shadowing-names
	def select_range(start: int, end: int) -> None:
		step = 1 if end >= start else -1

		for number in range(start, end + step, step):
			select_number(number)

	for selector in selectors:
		selector = selector.strip()

		if not selector:
			continue

		relative_match = re.fullmatch(r"(\d+)([+-])(\d+)", selector)

		if relative_match:
			start = int(relative_match.group(1))
			offset = int(relative_match.group(3))

			if relative_match.group(2) == "+":
				end = start + offset
			else:
				end = start - offset

			select_range(start, end)
			continue

		range_match = re.fullmatch(r"(\d+)-(\d+)", selector)

		if range_match:
			start = int(range_match.group(1))
			end = int(range_match.group(2))

			select_range(start, end)
			continue

		if selector.isdigit():
			select_number(int(selector))
			continue

		identifier = os.path.expanduser(selector).lower()

		exact_path = [
			(path, project)
			for path, project in projects.items()
			if path.lower() == identifier
		]

		if len(exact_path) == 1:
			add_project(exact_path[0][0])
			continue

		exact_name = [
			(path, project)
			for path, project in projects.items()
			if Path(path).name.lower() == identifier
		]

		if len(exact_name) == 1:
			add_project(exact_name[0][0])
			continue

		matches = [
			(path, project)
			for path, project in projects.items()
			if (identifier in Path(path).name.lower() or identifier in path.lower())
		]

		if not matches:
			print(f"[ERROR] project '{selector}' was not found")
			continue

		if len(matches) > 1:
			print(f"[ERROR] multiple projects match '{selector}':")

			for path, project in matches:
				print(
					f"  ID {project['id']} | TID {project['tid']} | {Path(path).name} | {path}"
				)

			continue

		add_project(matches[0][0])

	return selected


def filter_projects(projects: Projects, filters: list[str]) -> Projects:
	if not filters:
		return projects

	filtered: Projects = dict(projects)

	for expression in filters:
		expression = expression.strip()

		if len(expression) < 4:
			continue

		action = expression[0]
		filter_type = expression[1].lower()
		value = expression[3:]

		if action not in ("+", "-"):
			continue

		if filter_type not in ("m", "r"):
			print(f"[ERROR] invalid filter '{expression}'")
			continue

		if not value:
			continue

		matches: set[str] = set()

		if filter_type == "m":
			value = value.lower()

			matches = {
				path
				for path in filtered
				if (value in Path(path).name.lower() or value in path.lower())
			}

		elif filter_type == "r":
			try:
				pattern = re.compile(value, re.IGNORECASE)
			except re.error as error:
				print(f"[ERROR] invalid regex '{value}': {error}")
				continue

			matches = {path for path in filtered if pattern.search(Path(path).name)}

		if action == "+":
			filtered = {
				path: project for path, project in filtered.items() if path in matches
			}

		else:
			filtered = {
				path: project for path, project in filtered.items() if path not in matches
			}

	return filtered


def print_projects(
	projects: Projects, settings: Settings, options: ListOptions | None = None
) -> None:
	if not projects:
		print("no projects found")
		return

	if options is None:
		options = {}

	headers = {
		"id": "ID",
		"tid": "TID",
		"name": "NAME",
		"path": "PATH",
		"status": "STATUS",
		"last_touched": "LAST TOUCHED",
	}

	list_limit = options.get("limit")

	if list_limit is None:
		list_limit = settings["display"]["list_limit"]

	compact: bool = settings["output"]["compact"]
	columns: list[str] = settings["display"]["columns"]
	show_notes: bool = settings["display"]["show_notes"]
	show_headers: bool = settings["display"]["show_headers"]
	absolute_paths: bool = settings["output"]["absolute_paths"]
	configured_filters: list[str] = settings["display"]["filter"]

	columns = [column for column in columns if column in headers]

	if not columns:
		print("no valid columns configured")
		return

	filtered_projects = filter_projects(
		projects,
		configured_filters,
	)

	search: str | None = options.get("search")

	if search is not None:
		search_lower = search.lower()

		filtered_projects = {
			path: project
			for path, project in filtered_projects.items()
			if (search_lower in Path(path).name.lower() or search_lower in path.lower())
		}

	name_regex: str | None = options.get("regex")

	if name_regex is not None:
		try:
			pattern = re.compile(name_regex, re.IGNORECASE)
		except re.error as error:
			print(f"[ERROR] invalid regex: {error}")
			return

		filtered_projects = {
			path: project
			for path, project in filtered_projects.items()
			if pattern.search(Path(path).name)
		}

	if not filtered_projects:
		print("no projects found")
		return

	sort_by: str = settings["sorting"]["by"]
	sort_direction: str = settings["sorting"]["direction"]

	if sort_by not in (
		"id",
		"name",
		"path",
		"status",
		"last_touched",
		"time",
	):
		sort_by = "name"

	reverse = sort_direction == "descending"

	def sort_key(item: tuple[str, Project]) -> str:
		path, project = item

		if sort_by == "id":
			return str(project["id"])

		if sort_by == "name":
			return Path(path).name.lower()

		if sort_by == "path":
			return path.lower()

		if sort_by in ("last_touched", "time"):
			return project["last_touched"]

		return project[sort_by].lower()

	sorted_projects = sorted(
		filtered_projects.items(),
		key=sort_key,
		reverse=reverse,
	)

	selected_projects = sorted_projects[:list_limit]

	rows = []

	for tid, (path, project) in enumerate(selected_projects, start=1):
		row = []

		for column in columns:
			if column == "id":
				value = str(project["id"])

			elif column == "tid":
				value = str(tid)

			elif column == "name":
				value = Path(path).name

			elif column == "path":
				value = path

				if not absolute_paths:
					value = os.path.relpath(path)

			else:
				value = project[column]

			row.append(value)

		rows.append((tid, path, project, row))

	widths = [
		max(
			len(headers[column]),
			*(len(row[3][i]) for row in rows),
		)
		for i, column in enumerate(columns)
	]

	vertical_separator: str = settings["display"]["vertical_separator"] or " "
	horizontal_separator: str = settings["display"]["horizontal_separator"] or " "

	if compact:
		vertical_separator = vertical_separator.strip()

	if show_headers:
		header = vertical_separator.join(
			headers[column].ljust(widths[i]) for i, column in enumerate(columns)
		)

		separator = vertical_separator.join(
			horizontal_separator * width for width in widths
		)

		print(header)
		print(separator)

	for tid, path, project, row in rows:
		print(
			vertical_separator.join(value.ljust(widths[i]) for i, value in enumerate(row))
		)

		note = project.get("note", "")

		if show_notes and note:
			print(f"    {GRAY}{note}{RESET}")


def find_projects(
	path: str, settings: Settings, projects: Projects | None = None
) -> Projects:
	if projects is None:
		projects = {}

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
			project_path = str(current_path)
			last_touched = get_last_touched_date(project_path)

			# Update existing project
			if project_path in projects:
				projects[project_path]["last_touched"] = (
					last_touched.strftime(time_format)
					if last_touched is not None
					else "unknown"
				)

			# Add  new project
			else:
				projects[project_path] = {
					"id": get_id(projects),
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
	identifier = os.path.expanduser(identifier).strip().lower()

	if identifier.isdigit():
		project_id = int(identifier)

		for path, project in projects.items():
			if project["id"] == project_id:
				return path, project

		print(f"[ERROR] no project with ID '{identifier}'")
		return None

	for path, project in projects.items():
		if path.lower() == identifier:
			return path, project

	for path, project in projects.items():
		if Path(path).name.lower() == identifier:
			return path, project

	matches = [
		(path, project)
		for path, project in projects.items()
		if (identifier in Path(path).name.lower() or identifier in path.lower())
	]

	if len(matches) == 1:
		return matches[0]

	if len(matches) > 1:
		print(f"[ERROR] multiple projects match '{identifier}':")

		for path, project in matches:
			print(f"  {project['id']} | {Path(path).name} | {path}")

		return None

	print(f"[ERROR] project '{identifier}' was not found")
	return None
