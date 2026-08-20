import sys

from src.projects import *
from src.tracker_data import *

from src.obj.pyproject import project
from src.obj.settings import settings, parse_setting_value

_AVAILABLE_ARGUMENTS = {
	"version",
	"v",
	"help",
	"h",
	"list",
	"l",
	"add",
	"a",
	"remove",
	"rm",
	"r",
	"check",
	"c",
	"edit",
	"e",
	"init",
	"i",
	"settings",
	"s",
	"config",
	"cc",
}


def main() -> None:
	args = sys.argv[1:]

	data: dict | False = load_data()
	if data is False:
		create_data()
		data = {}

	if len(args) == 0:
		print_projects(data, settings)
		return

	verbose: bool = settings["logging"]["always_verbose"]

	done: set[int] = set()

	# Mark the argument to skip over it later
	for i, arg in enumerate(args):
		if arg.lower().strip("-") in ("verbose", "vv"):
			verbose = True
			done.add(i)

	for i in range(len(sys.argv[1:])):
		if i in done:
			continue

		arg = args[i].lower().strip("-")
		match arg:
			case "version" | "v":
				print(
					f"Project tracker v{project['version']} created by {project['authors'][0]['name']}"
				)

			case "help" | "h":
				print_help(project)

			# project id | project dir name | status | last touched date
			# Person can add their own statuses f.e 'final', 'maintenance', 'completed', etc.
			# last touched date - newest date a file was touched in the project
			case "list" | "l":
				options: dict[str, Any] = {}
				list_settings = settings

				j = i + 1

				while j < len(args):
					option = args[j]

					if option.lower().strip("-") in _AVAILABLE_ARGUMENTS:
						break

					override = option.lstrip("-")

					if "=" in override:
						key, raw_value = override.split("=", 1)

						try:
							value = parse_setting_value(raw_value)
							list_settings = list_settings.override(key, value)

							done.add(j)
							j += 1

							continue

						except KeyError:
							print(f"[ERROR] unknown setting '{key}'")
							break

					if option.isdigit():
						list_settings = list_settings.override(
							"display.list_limit",
							int(option),
						)

						done.add(j)
						j += 1

						continue

					if option.lower() == "regex":
						if j + 1 >= len(args):
							print("[ERROR] regex requires a pattern")
							break

						options["regex"] = args[j + 1]
						done.update({j, j + 1})
						j += 2
						continue

					options["search"] = option
					done.add(j)
					j += 1

				print_projects(data, list_settings, options)

			case "add" | "a":
				if i + 1 >= len(args):
					print("[ERROR] add requires a path")
					break

				path = Path(os.path.expanduser(args[i + 1])).resolve()
				done.add(i + 1)

				if not path.exists():
					print("[ERROR] the path does not exist")
					break

				if not path.is_dir():
					print("[ERROR] the path is not a directory")
					break

				status: str = settings["projects"]["default_status"]

				if i + 2 < len(args):
					status = args[i + 2]
					done.add(i + 2)

				note: str = ""

				if i + 3 < len(args):
					note = " ".join(args[i + 3 :])
					done.update(range(i + 3, len(args)))

				git_dir = path / ".git"

				if git_dir.is_dir() or git_dir.is_file():
					project_path = str(path)

					if project_path in data:
						print("[ERROR] project already exists")
						break

					last_touched = get_last_touched_date(project_path)

					data[project_path] = {
						"id": get_id(data),
						"path": project_path,
						"status": status,
						"last_touched": (
							last_touched.strftime(settings["display"]["time_format"])
							if last_touched is not None
							else "unknown"
						),
						"note": note,
					}

					save_data(data)

					print(f"added {path.name} ({data[project_path]['id']})")
					break

				print(f"scanning {path} for projects...")

				existing_paths = set(data)

				projects = find_projects(str(path), settings, data)

				new_projects = [
					project_path
					for project_path in projects
					if project_path not in existing_paths
				]

				if not new_projects:
					print("no new projects found")
					break

				for project_path in new_projects:
					projects[project_path]["status"] = status
					projects[project_path]["note"] = note

				data = projects

				save_data(data)

				print(f"added {len(new_projects)} projects")

				for project_path in new_projects:
					project_data = data[project_path]
					print(f"  {project_data['id']} | {Path(project_path).name}")

			case "remove" | "rm" | "r":
				if i + 1 >= len(args):
					print("[ERROR] remove requires a project")
					break

				identifier = args[i + 1]
				done.add(i + 1)

				# Basically clear the database
				if identifier.lower().strip("-") in ("all", "a"):
					how_many = len(data.keys())

					create_data()

					print(f"removed {how_many} entries")
					break

				found = get_project(data, identifier)

				if found is None:
					print(f"[ERROR] project '{identifier}' was not found")
					break

				project_path, _ = found

				del data[project_path]
				save_data(data)

				print(f"removed {Path(project_path).name}")

			case "check" | "cc":
				if i + 1 >= len(args):
					print("[ERROR] check requires a project")
					break

				identifier = args[i + 1]
				done.add(i + 1)

				found = get_project(data, identifier)

				if found is None:
					print(f"[ERROR] project '{identifier}' was not found")
					break

				project_path, project_data = found

				print(f"id:            {project_data['id']}")
				print(f"name:          {Path(project_path).name}")
				print(f"path:          {project_path}")
				print(f"status:        {project_data['status']}")
				print(f"last touched:  {project_data['last_touched']}")

				note = project_data.get("note", "")

				if note:
					print(f"note:          {note}")

			case "edit" | "e":
				if i + 1 >= len(args):
					print("[ERROR] edit requires a project")
					break

				identifier = args[i + 1]
				done.add(i + 1)

				if identifier.lower().strip("-") in ("all", "a"):
					selected_projects = data

				else:
					selected_projects = select_projects(
						data,
						settings,
						[identifier],
					)

				if not selected_projects:
					print("[ERROR] no projects selected")
					break

				j = i + 2
				changed: bool = False

				while j < len(args):
					field = args[j].lower()

					if field == "status":
						if j + 1 >= len(args):
							print("[ERROR] edit status requires a value")
							break

						status = args[j + 1]

						for project_data in selected_projects.values():
							project_data["status"] = status

						done.update({j, j + 1})
						changed = True
						j += 2

					elif field == "note":
						if j + 1 >= len(args):
							print("[ERROR] edit note requires a value")
							break

						note = " ".join(args[j + 1 :])

						for project_data in selected_projects.values():
							project_data["note"] = note

						done.update(range(j, len(args)))
						changed = True
						break

					else:
						print(f"[ERROR] unknown edit field '{args[j]}'")
						break

				if changed:
					save_data(data)

					if identifier.lower().strip("-") in ("all", "a"):
						print(f"edited {len(selected_projects)} projects")
					else:
						print(
							f"edited {Path(next(iter(selected_projects))).name if len(selected_projects) == 1 and identifier.lower().strip('-') not in ('all', 'a') else f'{len(selected_projects)} projects'}"
						)

			case "init" | "i":
				specific_path = args[i + 1] if i + 1 < len(args) else os.getcwd()

				if i + 1 < len(args):
					done.add(i + 1)

				path = os.path.expanduser(specific_path)

				if not os.path.exists(path):
					print("[ERROR] the path does not exist")
					break

				print(f"Scanning {os.path.abspath(path)}...")

				projects = find_projects(path, settings)

				if not projects:
					print("no projects found.")
					break

				print(f"found {len(projects)} projects.")

				print("saving projects...")
				data = projects
				save_data(data)
				print("done")

			case "settings" | "s" | "config" | "c":
				if i + 1 >= len(args):
					settings.display()
					break

				action = args[i + 1].lower().strip("-")
				done.add(i + 1)

				match action:
					case "edit" | "e":
						settings.edit()

					case _:
						print(f"[ERROR] unknown settings action '{args[i + 1]}'")

			# If the argument is not found maybe find the project?
			case _:
				identifier = args[i]

				found = get_project(data, identifier)

				if found is None:
					print(f"[ERROR] invalid argument")
					break

				project_path, project_data = found

				print(f"name:          {Path(project_path).name}")
				print(f"path:          {project_path}")
				print(f"status:        {project_data['status']}")
				print(f"last touched:  {project_data['last_touched']}")

				note = project_data.get("note", "")

				if note:
					print(f"note:          {note}")


if __name__ == "__main__":
	main()
else:
	print("please run this program from the command line")
