from typing import Any, NotRequired, TypedDict


class Project(TypedDict):
	id: int

	path: str
	status: str
	last_touched: str

	note: NotRequired[str]

	first_seen: NotRequired[str]
	deleted_at: NotRequired[str]

	archived: NotRequired[bool]
	archived_note: NotRequired[str]


Projects = dict[str, Project]

TRANSIENT_FIELDS = ("tid",)

UNKNOWN_TIME = "unknown"


def get_id(projects: Projects) -> int:
	if not projects:
		return 1

	known = [
		project["id"]
		for project in projects.values()
		if isinstance(project.get("id"), int)
	]

	if not known:
		return 1

	return max(known) + 1


def new_project(
	path: str,
	*,
	status: str,
	last_touched: str = UNKNOWN_TIME,
	note: str = "",
	project_id: int = 0,
	first_seen: str = "",
) -> Project:
	project: Project = {
		"id": project_id,
		"path": path,
		"status": status,
		"last_touched": last_touched,
		"note": note,
	}

	if first_seen:
		project["first_seen"] = first_seen

	return project


def normalise(projects: Any) -> Projects:
	if not isinstance(projects, dict):
		return {}

	cleaned: Projects = {}
	used_ids: set[int] = set()

	for path, project in projects.items():
		if not isinstance(path, str) or not isinstance(project, dict):
			continue

		for field in TRANSIENT_FIELDS:
			project.pop(field, None)

		project_id = project.get("id")

		if not isinstance(project_id, int) or project_id in used_ids:
			project_id = max(used_ids, default=0) + 1

		used_ids.add(project_id)

		project["id"] = project_id
		project["path"] = str(project.get("path") or path)
		project["status"] = str(project.get("status") or "unknown")
		project["last_touched"] = str(project.get("last_touched") or UNKNOWN_TIME)
		project["note"] = str(project.get("note") or "")

		if "archived" in project:
			project["archived"] = bool(project["archived"])

		cleaned[path] = project

	return cleaned


def is_archived(project: Project) -> bool:
	return bool(project.get("archived", False))
