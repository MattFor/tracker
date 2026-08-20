import os
import copy
import time

from pathlib import Path

from src.obj.settings import settings
from src.projects import find_projects, Projects
from src.tracker_data import create_data, load_data, save_data


def update_database(paths: list[str], data: Projects) -> tuple[Projects, bool, list[str]]:
	before = copy.deepcopy(data)
	before_paths = set(data)

	for path in paths:
		path = os.path.expanduser(path)

		if not os.path.exists(path):
			print(f"[ERROR] daemon path does not exist: {path}")
			continue

		if not os.path.isdir(path):
			print(f"[ERROR] daemon path is not a directory: {path}")
			continue

		data = find_projects(path, settings, data)

	new_projects = [path for path in data if path not in before_paths]

	changed = data != before

	if changed:
		save_data(data)

	return data, changed, new_projects


def main() -> None:
	paths: list[str] = settings["daemon"]["paths"]
	interval: int = settings["daemon"]["interval"]
	timestamp_format: str = settings["daemon"]["timestamp_format"]

	if not paths:
		print("[ERROR] no daemon paths configured")
		print("add paths to [daemon] in settings.toml")
		return

	if interval < 1:
		interval = 60

	data: Projects | False = load_data()

	if data is False:
		create_data()
		data = {}

	paths = [os.path.abspath(os.path.expanduser(path)) for path in paths]

	print("watching:")
	for path in paths:
		print(f"- {path}")

	print(f"scan interval: {interval}s")
	print("ctrl+c to stop")

	try:
		while True:
			started = time.monotonic()

			data, changed, new_projects = update_database(paths, data)

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
					f"[{timestamp}] added {len(project_rows)} new project{'s' if len(project_rows) > 1 else ''}:"
				)

				for project_id, name, project_path in project_rows:
					print(f"  {project_id:<4} {name:<{name_width}}  {project_path}")
			elif changed:
				print(f"[{timestamp}] database updated")
			else:
				print(f"[{timestamp}] no changes")

			elapsed = time.monotonic() - started
			time.sleep(max(0, interval - elapsed))

	except KeyboardInterrupt:
		print("\nstopped")


if __name__ == "__main__":
	main()
