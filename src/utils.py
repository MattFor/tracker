import os

from src.ansi import *
from pathlib import Path

from datetime import datetime


#
# File System
#


def walk(path: str, proj: str) -> dict | False:
	if not os.path.exists(path):
		return False

	try:
		for root, dirs, files in os.walk(path):
			# noinspection shadowing-builtins
			for dir in dirs:
				if dir.lower() == proj.lower():
					return {
						"path": dir,
					}
	except FileNotFoundError:
		return False
	except OSError:
		return False

	return False


def get_last_touched_date(path: str) -> datetime | None:
	if not os.path.exists(path):
		return None

	latest: float | None = None

	try:
		for root, _, files in os.walk(path):
			for file in files:
				file_path = Path(root) / file
				mtime = file_path.stat().st_mtime

				if latest is None or mtime > latest:
					latest = mtime

	except (FileNotFoundError, OSError):
		return None

	if latest is None:
		return None

	return datetime.fromtimestamp(latest)


#
# Printing
#


# Warning: !Only thing an LLM was used for! cause I am NOT writing allat by hand (i obv reviewed and made it better tho)
def print_help(project: dict) -> None:
	path = Path(__file__).resolve().parent.parent / "man" / "help.txt"

	try:
		text = path.read_text()
	except OSError as error:
		print(f"[ERROR] could not read help file: {error}")
		return

	replacements = {
		"PROJECT_NAME": project["name"].capitalize(),
		"PROJECT_VERSION": project["version"],
		"PROJECT_AUTHOR": project["authors"][0]["name"],
		"BOLD": BOLD,
		"CYAN": CYAN,
		"GRAY": GRAY,
		"GREEN": GREEN,
		"YELLOW": YELLOW,
		"MAGENTA": MAGENTA,
		"RESET": RESET,
	}

	for key, value in replacements.items():
		text = text.replace(f"{{{key}}}", str(value))

	print(text)


#
# Other
#


class Unknown:
	def __getitem__(self, key: str) -> "Unknown":
		return self

	def __str__(self) -> str:
		return "unknown"

	def __repr__(self) -> str:
		return "unknown"

	def __bool__(self) -> bool:
		return False
