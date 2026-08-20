import sys

from src.projects import *
from src.tracker_data import *


def main() -> None:
	settings: dict | False = load_settings()
	if settings is False:
		# Make a default settings object - TODO
		create_settings()
		settings = {}

	# if settings["mode"] == "auto":
	# 	pass
	# else:
	# 	pass

	data: dict | False = load_data()
	if data is False:
		create_data()
		data = {}

	args = sys.argv[1:]

	if len(args) == 0:
		print_projects(data, settings)
		return

	# this does not appear in done TODO
	verbose: bool = any(x in args for x in ("--verbose", "verbose", "-v", "v"))

	done: set[int] = set()

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
				print_projects(data, settings)

			case "add" | "a":
				pass

			case "remove" | "rm" | "r":
				pass

			# See the information of a single entry
			case "check" | "c":
				pass

			case "init" | "i":
				specific_path = args[i + 1] if i + 1 < len(args) else os.getcwd()

				if i + 1 < len(args):
					done.add(i + 1)

				path = os.path.expanduser(specific_path)

				if not os.path.exists(path):
					print("[ERROR] the path does not exist")
					break

				print(f"Scanning {os.path.abspath(path)}...")

				projects = find_projects(path)

				if not projects:
					print("no projects found.")
					break

				print(f"found {len(projects)} projects.")

				print("saving projects...")
				data = projects
				save_data(data)
				print("done")

			case _:
				print(f"argument {i} is invalid")


if __name__ == "__main__":
	main()
else:
	print("please run this program from the command line")
