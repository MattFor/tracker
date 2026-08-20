import os
import copy
import time

from pathlib import Path

from src.obj.settings import settings
from src.projects import find_projects, get_id, Projects
from src.tracker_data import create_data, load_data, save_data


def update_database(
	paths: list[str], data: Projects, archive: bool
) -> tuple[Projects, bool, list[str], list[str]]:
	before = copy.deepcopy(data)
	before_paths = set(data)

	valid_paths: list[Path] = []
	found_paths: set[str] = set()

	for path in paths:
		path = Path(os.path.expanduser(path)).resolve()

		if not path.exists():
			print(f"[ERROR] daemon path does not exist: {path}")
			continue

		if not path.is_dir():
			print(f"[ERROR] daemon path is not a directory: {path}")
			continue

		valid_paths.append(path)

		scanned = find_projects(str(path), settings)

		found_paths.update(scanned)

		for project_path, scanned_project in scanned.items():
			if project_path in data:
				project_data = data[project_path]

				project_data["last_touched"] = scanned_project["last_touched"]

				if project_data.get("archived", False):
					project_data["archived"] = False

					archived_note = project_data.get("archived_note", "")
					project_data["note"] = archived_note

					project_data.pop("archived_note", None)
					project_data.pop("deleted_at", None)

			else:
				scanned_project["id"] = get_id(data)
				scanned_project["first_seen"] = time.strftime(
					settings["daemon"]["timestamp_format"]
				)
				scanned_project["archived"] = False

				data[project_path] = scanned_project

	removed_projects: list[str] = []

	for project_path in list(data):
		project = Path(project_path)

		if not any(project.is_relative_to(path) for path in valid_paths):
			continue

		if project_path in found_paths:
			continue

		project_data = data[project_path]

		if archive:
			if project_data.get("archived", False):
				continue

			timestamp = time.strftime(settings["daemon"]["timestamp_format"])

			original_note = project_data.get("note", "")

			project_data["archived"] = True
			project_data["deleted_at"] = timestamp
			project_data["archived_note"] = original_note

			statistics = [
				f"ID: {project_data['id']}",
				f"Last touched: {project_data['last_touched']}",
			]

			first_seen = project_data.get("first_seen")

			if first_seen:
				statistics.append(f"First seen: {first_seen}")

			project_data["note"] = (
				f"[DELETED] ({timestamp})\n{chr(10).join(statistics)}{f'\n{original_note}' if original_note else ''}"
			)

			removed_projects.append(project_path)

		else:
			removed_projects.append(project_path)
			del data[project_path]

	new_projects = [
		project_path for project_path in data if project_path not in before_paths
	]

	changed = data != before

	if changed:
		save_data(data)

	return data, changed, new_projects, removed_projects


def main() -> None:
	archive: bool = settings["daemon"]["archive"]
	interval: int = settings["daemon"]["interval"]
	paths: list[str] = settings["daemon"]["paths"]
	timestamp_format: str = settings["daemon"]["timestamp_format"]

	if not paths:
		print(
			"\n[ERROR] no daemon paths configured; add them to [daemon] in settings.toml / my_settings.toml"
		)
		return

	if interval < 1:
		interval = 60

	data: Projects | False = load_data()

	if data is False:
		create_data()
		data = {}

	paths = [os.path.abspath(os.path.expanduser(path)) for path in paths]

	print("\nwatching:")
	for path in paths:
		print(f"- {path}")

	print(f"scan interval: {interval}s")
	print("ctrl+c to stop")

	try:
		while True:
			started = time.monotonic()

			data, changed, new_projects, removed_projects = update_database(
				paths, data, archive
			)

			timestamp = time.strftime(timestamp_format)

			if new_projects:
				project_rows = [
					(
						data[project_path]["id"],
						Path(project_path).name,
						project_path,
					)
					for project_path in new_projects
				]

				name_width = max(len(name) for _, name, _ in project_rows)

				print(
					f"[{timestamp}] added {len(project_rows)} new project{'s' if len(project_rows) != 1 else ''}:"
				)

				for project_id, name, project_path in project_rows:
					print(f"  {project_id:<4} {name:<{name_width}}  {project_path}")

			if removed_projects:
				project_rows = [
					(
						None,
						Path(project_path).name,
						project_path,
					)
					for project_path in removed_projects
				]

				name_width = max(len(name) for _, name, _ in project_rows)

				print(
					f"[{timestamp}] removed {len(project_rows)} project{'s' if len(project_rows) != 1 else ''}:"
				)

				for _, name, project_path in project_rows:
					print(f"  {'-':<4} {name:<{name_width}}  {project_path}")

			if not new_projects and not removed_projects and changed:
				print(f"[{timestamp}] database updated")

			elif not new_projects and not removed_projects:
				print(f"[{timestamp}] no changes")

			elapsed = time.monotonic() - started
			time.sleep(max(0, interval - elapsed))

	except KeyboardInterrupt:
		print("\nstopped")


if __name__ == "__main__":
	main()
