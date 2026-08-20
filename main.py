import os
import sys

import src.settings_and_data as settings

#
#  Directory walking
#


def walk(path: str, proj: str) -> dict | False:
	for root, dirs, files in os.walk(path):
		print(root)

		# noinspection shadowing-builtins
		for dir in dirs:
			if dir.lower() == proj.lower():
				return {
					"path": dir,
				}

	return False


def main() -> None:
	version: str | None = None

	# settings: dict = load_settings()
	#
	# if settings.mode == "auto":
	# 	pass
	# else:
	# 	pass

	if not os.path.exists("settings.json"):
		with open("settings.json", "r") as f:
			pass

	init: bool = False
	data: dict | None = None

	if not os.path.exists("data.pkl"):
		init = settings.create_data()

	cwd: str = os.getcwd()
	data = {} if init else load_data()

	args = sys.argv[1:]
	for i in range(len(sys.argv[1:])):
		arg = args[i]
		match arg:
			case "--help" | "help" | "-h" | "h":
				with open("pyproject.toml", "br") as f:
					version = tomllib.load(f)["project"]["version"]

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
				print(walk(args[i + 1], args[i + 2]))

			case _:  # Assume "list"
				print(data)


if __name__ == "__main__":
	main()
else:
	print("please run this program from the command line")
