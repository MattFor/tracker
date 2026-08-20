import sys

from src.utils import *
from src.projects import *
from src.pyproj import project

import src.settings_and_data as settings


def main() -> None:
	# settings.create_settings()
	# settings: dict = load_settings()
	#
	# if settings.mode == "auto":
	# 	pass
	# else:
	# 	pass

	cwd: str = os.getcwd()

	data = settings.load_data()

	if data is False:
		settings.create_data()
		data = {}

	args = sys.argv[1:]

	if len(args) == 0:
		print_projects(data)
		return

	verbose: bool = any(x in args for x in ("--verbose", "verbose", "-v", "v"))

	done: set[int] = set()

	for i in range(len(sys.argv[1:])):
		if i in done:
			continue

		arg = args[i]
		match arg:
			case "--version" | "version" | "-v" | "v":
				print(
					f"Project tracker v{project['version']} created by {project['authors'][0]['name']}"
				)

			case "--help" | "help" | "-h" | "h":
				print_help(project)

			# project id | project dir name | status | last touched date
			# Person can add their own statuses f.e 'final', 'maintenance', 'completed', etc.
			# last touched date - newest date a file was touched in the project
			case "--list" | "list" | "-l" | "l":
				print_projects(data)

			case "--add" | "add" | "-a" | "a":
				pass

			case "--remove" | "remove" | "--rm" | "rm" | "-r" | "r":
				pass

			# See the information of a single entry
			case "--check" | "check" | "-c" | "c":
				pass

			case "--init" | "init" | "-i" | "i":
				specific_path = args[i + 1] if i + 1 < len(args) else cwd

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
				settings.save_data(data)
				print("done")

			case _:  # Assume "list"
				print_projects(data)


if __name__ == "__main__":
	main()
else:
	print("please run this program from the command line")
