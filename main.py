import os
import sys

from src.pyproj import project

import src.sys_utils as sutils
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
	for i in range(len(sys.argv[1:])):
		arg = args[i]
		match arg:
			case "--version" | "version" | "-v" | "v":
				print(
					f"Project tracker v{project['version']} created by {project['authors'][0]['name']}"
				)

			case "--help" | "help" | "-h" | "h":
				version = settings.load_pyproject_toml()["project"]["version"]

				print(version)

			case "--list" | "list" | "-l" | "l":
				for key, value in data.items():
					print(f"{key}: {value}")

			case "--add" | "add" | "-a" | "a":
				pass

			case "--remove" | "remove" | "--rm" | "rm" | "-r" | "r":
				pass

			# See the information of a single entry
			case "--check" | "check" | "-c" | "c":
				pass

			case "find":
				print(sutils.walk(args[i + 1], args[i + 2]))

			case _:  # Assume "list"
				print(data)


if __name__ == "__main__":
	main()
else:
	print("please run this program from the command line")
