import os
import re

from typing import Any, Callable
from pathlib import Path

from tracker.util.text import parse_time
from tracker.config.settings import Settings
from tracker.config.defaults import SORT_KEYS
from tracker.core.models import Project, Projects


#
# Sorting
#


def _sort_key(settings: Settings) -> Callable[[tuple[str, Project]], tuple[Any, str]]:
	sort_by: str = settings["sorting"]["by"]
	time_format: str = settings["display"]["time_format"]

	if sort_by not in SORT_KEYS:
		sort_by = "name"

	def key(item: tuple[str, Project]) -> tuple[Any, str]:
		path, project = item

		name = Path(path).name.lower()

		if sort_by == "id":
			return project.get("id", 0), name

		if sort_by == "name":
			return name, name

		if sort_by == "path":
			return path.lower(), name

		if sort_by in ("last_touched", "time"):
			moment = parse_time(project.get("last_touched", ""), time_format)

			return (moment.timestamp() if moment else float("-inf")), name

		return str(project.get(sort_by, "")).lower(), name

	return key


def sort_projects(projects: Projects, settings: Settings) -> list[tuple[str, Project]]:
	reverse = settings["sorting"]["direction"] == "descending"

	return sorted(projects.items(), key=_sort_key(settings), reverse=reverse)


def temporary_ids(projects: Projects, settings: Settings) -> dict[str, int]:
	return {
		path: tid for tid, (path, _) in enumerate(sort_projects(projects, settings), 1)
	}


#
# Filtering
#


def filter_projects(projects: Projects, filters: list[str]) -> Projects:
	if not filters:
		return projects

	filtered: Projects = dict(projects)

	for expression in filters:
		expression = expression.strip()

		if len(expression) < 4 or expression[2] != ":":
			if expression:
				print(f"[ERROR] invalid filter '{expression}', expected +m:value")

			continue

		action = expression[0]
		filter_type = expression[1].lower()
		value = expression[3:]

		if action not in ("+", "-"):
			print(f"[ERROR] invalid filter '{expression}', must start with + or -")
			continue

		if filter_type not in ("m", "r"):
			print(f"[ERROR] invalid filter '{expression}', type must be m or r")
			continue

		if not value:
			continue

		matches: set[str] = set()

		if filter_type == "m":
			needle = value.lower()

			matches = {
				path
				for path in filtered
				if needle in Path(path).name.lower() or needle in path.lower()
			}

		else:
			try:
				pattern = re.compile(value, re.IGNORECASE)
			except re.error as error:
				print(f"[ERROR] invalid regex '{value}': {error}")
				continue

			matches = {path for path in filtered if pattern.search(Path(path).name)}

		if action == "+":
			filtered = {path: p for path, p in filtered.items() if path in matches}
		else:
			filtered = {path: p for path, p in filtered.items() if path not in matches}

	return filtered


def search_projects(projects: Projects, search: str) -> Projects:
	needle = search.lower()

	return {
		path: project
		for path, project in projects.items()
		if needle in Path(path).name.lower() or needle in path.lower()
	}


def regex_projects(projects: Projects, expression: str) -> Projects | None:
	try:
		pattern = re.compile(expression, re.IGNORECASE)
	except re.error as error:
		print(f"[ERROR] invalid regex: {error}")
		return None

	return {
		path: project
		for path, project in projects.items()
		if pattern.search(Path(path).name)
	}


#
# Selecting
#


# 5+3  -> project 5 and the next 3
_RELATIVE = re.compile(r"(\d+)\+(\d+)")

# 3-7  -> projects 3 through 7 inclusive (in either direction)
_RANGE = re.compile(r"(\d+)-(\d+)")

# #5 always means the permanent ID | @5 always means the temporary ID
_EXPLICIT = re.compile(r"([#@])(\d+)")

ALL_SELECTORS = ("all", "*")


def select_projects(
	projects: Projects,
	settings: Settings,
	selectors: list[str],
	*,
	quiet: bool = False,
) -> Projects:
	ordered = sort_projects(projects, settings)

	temporary_ids = {path: tid for tid, (path, _) in enumerate(ordered, 1)}
	by_tid = {tid: path for path, tid in temporary_ids.items()}

	selected: Projects = {}
	preference: str = settings["projects"]["conflict_resolution_preference"]

	def report(message: str) -> None:
		if not quiet:
			print(message)

	# noinspection shadowing-names
	def show(matches: list[tuple[str, Project]]) -> None:
		from tracker.ui.render import render_rows

		for line in render_rows(matches, settings, temporary_ids, show_headers=False, prefix="  "):
			report(line)

	def find_number(number: int, source: str = "any") -> list[tuple[str, Project]]:
		by_id = [
			(path, project)
			for path, project in projects.items()
			if project.get("id") == number
		]

		path = by_tid.get(number)
		by_temporary = [(path, projects[path])] if path is not None else []

		if source == "id":
			return by_id

		if source == "tid":
			return by_temporary

		if by_id and by_temporary and by_id[0][0] != by_temporary[0][0]:
			return by_id + by_temporary

		return by_id or by_temporary

	def select_number(number: int, source: str = "any", complain: bool = True) -> bool:
		# noinspection shadowing-names
		matches = find_number(number, source)

		if not matches:
			if complain:
				report(f"[ERROR] no project matches ID/TID '{number}'")

			return False

		if len(matches) > 1:
			report(f"[ERROR] '{number}' is both an ID and a TID:")
			show(matches)
			report(f"        use #{number} for the ID or @{number} for the TID")

			return False

		selected[matches[0][0]] = matches[0][1]

		return True

	# noinspection shadowing-names
	def select_range(start: int, end: int) -> None:
		step = 1 if end >= start else -1

		found = False

		for number in range(start, end + step, step):
			if number < 1:
				continue

			found = select_number(number, complain=False) or found

		if not found:
			report(f"[ERROR] no projects in the range '{start}-{end}'")

	for selector in selectors:
		selector = selector.strip()

		if not selector:
			continue

		if selector.lower() in ALL_SELECTORS:
			selected.update(projects)
			continue

		explicit = _EXPLICIT.fullmatch(selector)

		if explicit:
			source = "id" if explicit.group(1) == "#" else "tid"
			select_number(int(explicit.group(2)), source)
			continue

		relative = _RELATIVE.fullmatch(selector)

		if relative:
			start = int(relative.group(1))
			select_range(start, start + int(relative.group(2)))
			continue

		span = _RANGE.fullmatch(selector)

		if span:
			select_range(int(span.group(1)), int(span.group(2)))
			continue

		if selector.isdigit():
			select_number(int(selector))
			continue

		identifier = os.path.expanduser(selector).lower().rstrip("/")

		exact_path = [
			(path, project)
			for path, project in projects.items()
			if path.lower().rstrip("/") == identifier
		]

		if len(exact_path) == 1:
			selected[exact_path[0][0]] = exact_path[0][1]
			continue

		exact_name = [
			(path, project)
			for path, project in projects.items()
			if Path(path).name.lower() == identifier
		]

		if len(exact_name) == 1:
			selected[exact_name[0][0]] = exact_name[0][1]
			continue

		matches = [
			(path, project)
			for path, project in projects.items()
			if identifier in Path(path).name.lower() or identifier in path.lower()
		]

		if not matches:
			report(f"[ERROR] project '{selector}' was not found")
			continue

		if len(matches) == 1:
			selected[matches[0][0]] = matches[0][1]
			continue

		if preference == "starts_with":
			starts_with = [
				(path, project)
				for path, project in matches
				if Path(path).name.lower().startswith(identifier)
			]

			if len(starts_with) == 1:
				selected[starts_with[0][0]] = starts_with[0][1]
				continue

			if starts_with:
				matches = starts_with

		if preference == "first_match":
			ranked = sorted(matches, key=lambda item: temporary_ids.get(item[0], 0))

			selected[ranked[0][0]] = ranked[0][1]
			continue

		report(f"[ERROR] multiple projects match '{selector}':")
		show(matches)

	return selected
