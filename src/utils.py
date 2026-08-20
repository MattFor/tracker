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


def print_help(project: dict) -> None:
	print(f"""{BOLD}{CYAN}{project["name"].capitalize()} v{project["version"]}{RESET} {GRAY}Created by {project["authors"][0]["name"]}{RESET}

{BOLD}Usage:{RESET}
	{GREEN}tracker <command> [arguments] [options]{RESET}

{BOLD}Arguments:{RESET}
	{YELLOW}help{RESET}, {GRAY}-h, --help{RESET}
		Show this help message.

	{YELLOW}version{RESET}, {GRAY}-v, --version{RESET}
		Show the application version.
					
	{YELLOW}list{RESET}, {GRAY}-l, --list{RESET}
		List all tracked projects.
					
	{YELLOW}add{RESET}, {GRAY}-a, --add{RESET}
		Add a project to the tracker.
					
	{YELLOW}remove{RESET}, {GRAY}-r, --remove, --rm{RESET}
		Remove a project from the tracker.
					
	{YELLOW}check{RESET}, {GRAY}-c, --check{RESET}
		Show detailed information about a tracked project.

{GRAY}Usage:{RESET}
	{GREEN}tracker find <path> <project>{RESET}
				
{BOLD}Options:{RESET}
	{MAGENTA}verbose{RESET}, {GRAY}-V, --verbose{RESET}
		Enable verbose output.
				
{BOLD}Examples:{RESET}
	{GREEN}tracker list{RESET}
	{GREEN}tracker add{RESET}
	{GREEN}tracker check my-project{RESET}
	{GREEN}tracker find ~/Programming my-project{RESET}
	{GREEN}tracker --version{RESET}
	{GREEN}tracker --help{RESET}
				""")


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
