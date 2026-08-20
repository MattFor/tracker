import sys

from src.utils import *
from src.pyproj import project

import src.settings_and_data as settings


def main() -> None:
	settings.create_settings()

	# settings: dict = load_settings()
	#
	# if settings.mode == "auto":
	# 	pass
	# else:
	# 	pass

	cwd: str = os.getcwd()
	init: bool = settings.create_data()
	data: dict | False = {} if init else settings.load_data()

	args = sys.argv[1:]

	verbose: bool = any(x in args for x in ("--verbose", "verbose", "-v", "v"))

	for i in range(len(sys.argv[1:])):
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
				for k, v in data.items():
					print(f"{k} | {v}")

			case "--add" | "add" | "-a" | "a":
				pass

			case "--remove" | "remove" | "--rm" | "rm" | "-r" | "r":
				pass

			# See the information of a single entry
			case "--check" | "check" | "-c" | "c":
				pass

			case "find":
				print(walk(args[i + 1], args[i + 2]))

			case _:  # Assume "list"
				print(data)


if __name__ == "__main__":
	main()
else:
	print("please run this program from the command line")
