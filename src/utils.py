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
	print(f"""{BOLD}{CYAN}{project["name"].capitalize()} v{project["version"]}{RESET}{GRAY}Created by {project["authors"][0]["name"]}{RESET}

{BOLD}Usage:{RESET}
	{GREEN}tracker <command> [arguments] [options]{RESET}

{BOLD}Commands:{RESET}

	{YELLOW}help{RESET}, {GRAY}-h, --help{RESET}
		Show this.

	{YELLOW}version{RESET}, {GRAY}-v, --version{RESET}
		Show program version.

	{YELLOW}list{RESET}, {GRAY}-l, --list{RESET}
		List tracked projects.

		{GRAY}Usage:{RESET}
			{GREEN}tracker list{RESET}
			{GREEN}tracker list <search>{RESET}
			{GREEN}tracker list <number>{RESET}
			{GREEN}tracker list regex <pattern>{RESET}
			{GREEN}tracker list <setting>=<value>{RESET}

		{GRAY}Examples:{RESET}
			{GREEN}tracker list tracker{RESET}
			{GREEN}tracker list 20{RESET}
			{GREEN}tracker list regex "^relaxy-"{RESET}
			{GREEN}tracker list display.list_limit=20{RESET}
			{GREEN}tracker list sorting.by=time sorting.direction=descending{RESET}

		{GRAY}Multiple setting overrides may be used at once.{RESET}

	{YELLOW}add{RESET}, {GRAY}-a, --add{RESET}
		Add a project or scan a directory for projects.

		{GRAY}Usage:{RESET}
			{GREEN}tracker add <path>{RESET}
			{GREEN}tracker add <path> <status>{RESET}
			{GREEN}tracker add <path> <status> <note...>{RESET}

		{GRAY}If <path> is not a Git project, its subdirectories are searched for Git projects.{RESET}

	{YELLOW}remove{RESET}, {GRAY}-r, --remove, --rm{RESET}
		Remove a tracked project.

		{GRAY}Usage:{RESET}
			{GREEN}tracker remove <project>{RESET}

	{YELLOW}check{RESET}, {GRAY}cc{RESET}
		Show detailed information about a tracked project.

		{GRAY}Usage:{RESET}
			{GREEN}tracker check <project>{RESET}

	{YELLOW}edit{RESET}, {GRAY}-e, --edit{RESET}
		Edit one or more project properties.

		{GRAY}Usage:{RESET}
			{GREEN}tracker edit <selection> status <value>{RESET}
			{GREEN}tracker edit <selection> note <value...>{RESET}

		{GRAY}Selection can use:{RESET}
			{GREEN}<id>{RESET}              Permanent project ID
			{GREEN}<tid>{RESET}             Temporary display ID
			{GREEN}<n-x>{RESET}             Inclusive range
			{GREEN}<n+x>{RESET}             Select n and the next x projects
			{GREEN}<n-x>{RESET}             Select n and the previous x projects
			{GREEN}<name>{RESET}            Project name
			{GREEN}<path>{RESET}            Full or partial project path

		{GRAY}Examples:{RESET}
			{GREEN}tracker edit 12 status active{RESET}
			{GREEN}tracker edit 3-7 status completed{RESET}
			{GREEN}tracker edit 5+3 note "needs documentation"{RESET}
			{GREEN}tracker edit tracker status maintenance{RESET}
			{GREEN}tracker edit all status active{RESET}

	{YELLOW}init{RESET}, {GRAY}-i, --init{RESET}
		Scan a directory and discover projects.

		{GRAY}Usage:{RESET}
			{GREEN}tracker init <path>{RESET}

		{GRAY}If no path is supplied, the current directory is used.{RESET}

	{YELLOW}settings{RESET}, {GRAY}-s, --settings, config{RESET}
		View or edit the configuration.

		{GRAY}Usage:{RESET}
			{GREEN}tracker settings{RESET}
			{GREEN}tracker settings edit{RESET}

{BOLD}List filters:{RESET}
	{GRAY}Persistent filters can be configured in settings.toml.{RESET}

	{GREEN}+m:<value>{RESET}	Include matching names/paths.
	{GREEN}-m:<value>{RESET}	Exclude matching names/paths.
	{GREEN}+r:<regex>{RESET}	Include names matching a regex.
	{GREEN}-r:<regex>{RESET}	Exclude names matching a regex.

	{GRAY}Example:{RESET}
		{GREEN}filter = ["+m:python", "-m:test", "+r:^relaxy-"]{RESET}

{BOLD}Options:{RESET}
	{MAGENTA}verbose{RESET}, {GRAY}vv, --verbose, --vv{RESET}
		Enable verbose output.

{BOLD}Project selection:{RESET}
	{GRAY}Projects can generally be identified by:{RESET}
		{GREEN}ID{RESET}             Permanent global ID
		{GREEN}TID{RESET}            Temporary ID from the current sorted view
		{GREEN}name{RESET}           Exact or partial project name
		{GREEN}path{RESET}           Exact or partial project path

{BOLD}Examples:{RESET}
	{GREEN}tracker{RESET}
	{GREEN}tracker list{RESET}
	{GREEN}tracker list tracker{RESET}
	{GREEN}tracker list 20{RESET}
	{GREEN}tracker add ~/Programming/Projects active "work in progress"{RESET}
	{GREEN}tracker check tracker{RESET}
	{GREEN}tracker check 42{RESET}
	{GREEN}tracker edit 3-7 status completed{RESET}
	{GREEN}tracker edit all status active{RESET}
	{GREEN}tracker remove tracker{RESET}
	{GREEN}tracker init ~/Programming{RESET}
	{GREEN}tracker settings{RESET}
	{GREEN}tracker settings edit{RESET}
	"""
	)


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
