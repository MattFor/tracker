import sys
import signal
import subprocess

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
	"daemon",
	"daemonize",
	"daemonise",
	"background",
	"b",
	"dbg",
}


def kill_daemons() -> None:
	result = subprocess.run(
		["pgrep", "-f", r"-m src\.daemon(?:\s|$)"],
		capture_output=True,
		text=True,
	)

	if result.returncode != 0:
		print("no daemons running")
		return

	pids = []

	for line in result.stdout.splitlines():
		try:
			pid = int(line.strip())
		except ValueError:
			continue

		if pid != os.getpid():
			pids.append(pid)

	if not pids:
		print("no daemons running")
		return

	for pid in pids:
		try:
			os.kill(pid, signal.SIGTERM)
		except ProcessLookupError:
			continue
		except PermissionError:
			print(f"[ERROR] could not kill daemon {pid}")

	print(f"killed {len(pids)} daemon{'s' if len(pids) != 1 else ''}")


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

			case "check" | "cc":
				if i + 1 >= len(args):
					print("[ERROR] check requires a project")
					break

				identifier = args[i + 1]
				done.add(i + 1)

				selected_projects = select_projects(data, settings, [identifier])

				if not selected_projects:
					print("[ERROR] no projects selected")
					break

				if len(selected_projects) > 1:
					print("[ERROR] multiple projects selected")
					break

				project_path, project_data = next(iter(selected_projects.items()))

				print(format_project(project_path, project_data, settings))

				note = project_data.get("note", "")

				if note:
					print(f"    {GRAY}{note}{RESET}")

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

					print(
						f"added {format_project(project_path, data[project_path], settings)}"
					)
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
					print(f"  {format_project(project_path, project_data, settings)}")

			case "remove" | "rm" | "r":
				if i + 1 >= len(args):
					print("[ERROR] no project provided")
					break

				identifier = args[i + 1]
				done.add(i + 1)

				if identifier.lower().strip("-") in ("all", "a"):
					how_many = len(data)
					data = {}
					save_data(data)

					print(f"removed {how_many} entries")
					break

				selected_projects = select_projects(data, settings, [identifier])

				if not selected_projects:
					print("[ERROR] no projects selected")
					break

				removed_projects = dict(selected_projects)

				for project_path in selected_projects:
					del data[project_path]

				save_data(data)

				if len(removed_projects) == 1:
					project_path, project_data = next(iter(removed_projects.items()))

					print(
						f"removed {format_project(project_path, project_data, settings)}"
					)
				else:
					print(f"removed {len(removed_projects)} projects")

			case "edit" | "e":
				if i + 1 >= len(args):
					print("[ERROR] edit requires a project")
					break

				identifier = args[i + 1]
				done.add(i + 1)

				if identifier.lower().strip("-") in ("all", "a"):
					selected_projects = data

				else:
					selected_projects = select_projects(data, settings, [identifier])

				if not selected_projects:
					print("[ERROR] no projects selected")
					break

				changes: dict[str, tuple[str, str]] = {}
				j = i + 2

				while j < len(args):
					field = args[j].lower()

					if field == "status":
						if j + 1 >= len(args):
							print("[ERROR] edit status requires a value")
							break

						status = args[j + 1]

						for project_path, project_data in selected_projects.items():
							old_value = project_data["status"]

							if old_value != status:
								project_data["status"] = status

								if len(selected_projects) == 1:
									changes["status"] = (old_value, status)

						done.update({j, j + 1})
						j += 2

					elif field == "note":
						if j + 1 >= len(args):
							print("[ERROR] edit note requires a value")
							break

						note = " ".join(args[j + 1 :])

						for project_path, project_data in selected_projects.items():
							old_value = project_data.get("note", "")

							if old_value != note:
								project_data["note"] = note

								if len(selected_projects) == 1:
									changes["note"] = (old_value, note)

						done.update(range(j, len(args)))
						break

					else:
						print(f"[ERROR] unknown edit field '{args[j]}'")
						break

				if changes or len(selected_projects) > 1:
					save_data(data)

					if len(selected_projects) == 1:
						project_path = next(iter(selected_projects))

						print(
							f"edited {format_project(project_path, selected_projects[project_path], settings)}"
						)

						for field, (old_value, new_value) in changes.items():
							old_display = old_value or '""'
							new_display = new_value or '""'

							print(
								f"  {field}: {GRAY}{old_display}{RESET} -> {new_display}"
							)
					else:
						print(f"edited {len(selected_projects)} projects")

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

			case "daemon" | "d" | "daemonize" | "daemonise" | "background" | "b" | "bg":
				if i + 1 < len(args):
					action = args[i + 1].lower().strip("-")

					if action in ("kill", "k"):
						done.add(i + 1)
						kill_daemons()
						break

				daemon_path = Path(__file__).resolve().parent / "src" / "daemon.py"

				if not daemon_path.exists():
					print("[ERROR] daemon.py was not found")
					break

				subprocess.Popen(
					[sys.executable, "-m", "src.daemon"],
					cwd=Path(__file__).resolve().parent,
					start_new_session=True,
				)

				print("daemon started")

			# If the argument is not found maybe find the project?
			case _:
				identifier = args[i]

				selected_projects = select_projects(data, settings, [identifier])

				if not selected_projects:
					break

				if len(selected_projects) > 1:
					continue

				project_path, project_data = next(iter(selected_projects.items()))

				print(format_project(project_path, project_data, settings))

				note = project_data.get("note", "")

				if note:
					print(f"    {GRAY}{note}{RESET}")


if __name__ == "__main__":
	main()
else:
	print("please run this program from the command line")
