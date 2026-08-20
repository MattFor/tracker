from typing import TypedDict

from src.utils import *


class Project(TypedDict):
	path: str
	status: str
	last_touched: str


Projects = dict[str, Project]


def print_projects(projects: Projects, settings: dict) -> None:
	if not projects:
		print("no projects found")
		return

	headers = {
		"name": "NAME",
		"path": "PATH",
		"status": "STATUS",
		"last_touched": "LAST TOUCHED",
	}

	columns: list[str] = settings["columns"]
	list_entries: int = settings["list_entries"]

	columns = [column for column in columns if column in headers]

	selected_projects = list(projects.items())[:list_entries]

	rows = [
		[Path(path).name if column == "name" else project[column] for column in columns]
		for path, project in selected_projects
	]

	widths = [
		max(
			len(headers[column]),
			*(len(row[i]) for row in rows),
		)
		for i, column in enumerate(columns)
	]

	header = "  ".join(
		headers[column].ljust(widths[i]) for i, column in enumerate(columns)
	)

	separator = "  ".join("-" * width for width in widths)

	print(header)
	print(separator)

	for row in rows:
		print("  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))


def find_projects(path: str) -> Projects:
	projects: Projects = {}

	root_path = Path(path).expanduser().resolve()

	if not root_path.exists() or not root_path.is_dir():
		return projects

	for current_root, dirs, _ in os.walk(root_path):
		current_path = Path(current_root)
		git_dir = current_path / ".git"

		if git_dir.is_dir() or git_dir.is_file():
			last_touched = get_last_touched_date(str(current_path))
			project_path = str(current_path)

			projects[project_path] = {
				"path": project_path,
				"status": "unknown",
				"last_touched": (
					last_touched.strftime("%Y-%m-%d %H:%M:%S")
					if last_touched is not None
					else "unknown"
				),
			}

			# Don't search already found
			dirs[:] = []

	return projects
