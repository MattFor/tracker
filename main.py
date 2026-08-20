import sys

import json

import tomllib


def load_settings() -> dict:
	with open("settings.json", "r") as f:
		settings = json.load(f)
	return settings


def save_settings(settings: dict) -> None:
	with open("settings.json", "w") as f:
		json.dump(settings, f, indent=4)


def main() -> None:
	version: str | None = None
	# settings: dict = load_settings()
	#
	# if settings.mode == "auto":
	# 	pass
	# else:
	# 	pass

	for arg in sys.argv[1:]:
		match arg:
			case "--help" | "help" | "-h" | "h":
				with open("pyproject.toml", "b+r") as f:
					version = tomllib.load(f)["project"]["version"]
				print(version)
			case "test":
				print("output")
			case _:
				print("invalid argument")


if __name__ != "main":
	args = sys.argv[1:]
	main()
else:
	print("please run this program from the command line")
