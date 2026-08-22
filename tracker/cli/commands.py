import os
import sys
import time

from typing import Any
from pathlib import Path
from dataclasses import dataclass, field

from tracker.config.defaults import SECTION_TITLES, defaults
from tracker.config.settings import Settings, parse_setting_value
from tracker.config.writer import write_setting
from tracker.config.metadata import project as metadata
from tracker.core import daemon
from tracker.core.discovery import (
	find_projects,
	format_last_touched,
	get_last_touched_date,
	is_project,
)
from tracker.core.models import Projects, get_id, new_project
from tracker.core.selection import select_projects, temporary_ids
from tracker.core.storage import data_path, save_data
from tracker.ui.ansi import C
from tracker.ui.details import print_details
from tracker.ui.help import print_help
from tracker.ui.render import format_project, print_projects, render_rows
from tracker.util.text import parse_time, relative_time


@dataclass
class Context:
	settings: Settings
	data: Projects
	verbose: bool = False
	assume_yes: bool = False
	options: dict[str, Any] = field(default_factory=dict)

	def log(self, message: str) -> None:
		if self.verbose:
			print(f"{C.GRAY}[verbose] {message}{C.RESET}")

	def save(self) -> bool:
		return save_data(self.data, self.settings)

	def tids(self) -> dict[str, int]:
		return temporary_ids(self.data, self.settings)


def confirm(context: Context, question: str) -> bool:
	if context.assume_yes:
		return True

	if not context.settings["projects"]["confirm_destructive"]:
		return True

	if not sys.stdin.isatty():
		print("[ERROR] refusing to run without confirmation; pass --yes")
		return False

	try:
		answer = input(f"{question} [y/N] ").strip().lower()
	except (EOFError, KeyboardInterrupt):
		print()
		return False

	return answer in ("y", "yes")


#
# Information
#


def command_version(context: Context) -> int:
	print(f"{metadata.name.capitalize()} v{metadata.version} by {metadata.author}")

	if context.verbose:
		print(f"  settings  {context.settings.path}")
		print(f"  database  {data_path(context.settings)}")
		print(f"  python    {sys.version.split()[0]}")

	return 0


def command_help() -> int:
	print_help(metadata)
	return 0


#
# Listing
#


def command_list(context: Context, args: list[str]) -> int:
	settings = context.settings
	options: dict[str, Any] = {"filters": []}

	index = 0

	while index < len(args):
		token = args[index]
		stripped = token.lstrip("-")

		if "=" in stripped and not stripped.startswith(("+", "-")):
			key, _, raw = stripped.partition("=")

			try:
				settings = settings.override(key, parse_setting_value(raw))
				context.log(f"override {key} = {raw}")

			except KeyError:
				print(f"[ERROR] unknown setting '{key}'")
				return 1

			except ValueError as error:
				print(f"[ERROR] {error}")
				return 1

			index += 1
			continue

		if token.isdigit():
			settings = settings.override("display.list_limit", int(token))
			index += 1
			continue

		if token.lower() in ("regex", "re"):
			if index + 1 >= len(args):
				print("[ERROR] regex requires a pattern")
				return 1

			options["regex"] = args[index + 1]
			index += 2
			continue

		if len(token) > 3 and token[0] in "+-" and token[2] == ":":
			options["filters"].append(token)
			index += 1
			continue

		options["search"] = token
		index += 1

	context.log(f"listing from {data_path(settings)}")

	print_projects(context.data, settings, options)

	return 0


def command_check(context: Context, args: list[str]) -> int:
	if not args:
		print("[ERROR] check requires a project")
		return 1

	selected = select_projects(context.data, context.settings, args)

	if not selected:
		return 1

	tids = context.tids()

	for index, (path, project) in enumerate(selected.items()):
		if index:
			print()

		print_details(
			path,
			project,
			context.settings,
			tids.get(path, 0),
			verbose=context.verbose,
		)

	return 0


def command_show(context: Context, args: list[str]) -> int:
	selected = select_projects(context.data, context.settings, args)

	if not selected:
		return 1

	temporary_ids = context.tids()

	for line in render_rows(
		selected.items(), context.settings, temporary_ids, show_headers=False
	):
		print(line)

	return 0


def command_path(context: Context, args: list[str]) -> int:
	if not args:
		print("[ERROR] path requires a project")
		return 1

	selected = select_projects(context.data, context.settings, args)

	if not selected:
		return 1

	for path in selected:
		print(path)

	return 0


def command_stats(context: Context) -> int:
	data = context.data

	if not data:
		print("no projects tracked yet")
		return 0

	settings = context.settings
	time_format: str = settings["display"]["time_format"]

	statuses: dict[str, int] = {}

	for project in data.values():
		status = str(project.get("status", "unknown"))
		statuses[status] = statuses.get(status, 0) + 1

	archived = sum(1 for project in data.values() if project.get("archived"))
	missing = sum(1 for path in data if not Path(path).is_dir())

	print(f"{C.BOLD}Tracked projects{C.RESET}")
	print(f"  {'total'.ljust(14)}{len(data)}")

	if archived:
		print(f"  {'archived'.ljust(14)}{archived}")

	if missing:
		print(f"  {'missing'.ljust(14)}{missing}")

	print(f"\n{C.BOLD}By status{C.RESET}")

	for status, count in sorted(statuses.items(), key=lambda item: (-item[1], item[0])):
		print(f"  {status.ljust(14)}{count}")

	dated = [
		(parse_time(str(project.get("last_touched", "")), time_format), path)
		for path, project in data.items()
	]

	dated = [(moment, path) for moment, path in dated if moment is not None]

	if dated:
		newest = max(dated)
		oldest = min(dated)

		print(f"\n{C.BOLD}Activity{C.RESET}")
		print(
			f"  {'newest'.ljust(14)}{Path(newest[1]).name} ({relative_time(newest[0])})"
		)
		print(
			f"  {'oldest'.ljust(14)}{Path(oldest[1]).name} ({relative_time(oldest[0])})"
		)

	print(f"\n{C.GRAY}database: {data_path(settings)}{C.RESET}")

	return 0


#
# Changing the database
#


def command_add(context: Context, args: list[str]) -> int:
	if not args:
		print("[ERROR] add requires a path")
		return 1

	settings = context.settings
	data = context.data

	path = Path(os.path.expanduser(args[0])).resolve()

	if not path.exists():
		print(f"[ERROR] the path does not exist: {path}")
		return 1

	if not path.is_dir():
		print("[ERROR] the path is not a directory")
		return 1

	status = args[1] if len(args) > 1 else settings["projects"]["default_status"]
	note = " ".join(args[2:]) if len(args) > 2 else ""

	time_format: str = settings["display"]["time_format"]
	ignore = (
		settings["projects"]["ignore"]
		if settings["scan"]["timestamps_skip_ignored"]
		else ()
	)

	if is_project(path, settings["scan"]["detect_git"]):
		project_path = str(path)

		if project_path in data:
			print("[ERROR] this project is already tracked")
			print(
				format_project(project_path, data[project_path], settings, context.tids())
			)
			return 1

		data[project_path] = new_project(
			project_path,
			status=status,
			last_touched=format_last_touched(
				get_last_touched_date(project_path, ignore), time_format
			),
			note=note,
			project_id=get_id(data),
			first_seen=time.strftime(time_format),
		)

		if not context.save():
			return 1

		print(
			f"added {format_project(project_path, data[project_path], settings, context.tids())}"
		)

		return 0

	print(f"scanning {path} for projects...")

	known = set(data)

	find_projects(str(path), settings, data)

	added = [project_path for project_path in data if project_path not in known]

	if not added:
		print("no new projects found")
		return 0

	stamp = time.strftime(time_format)

	for project_path in added:
		data[project_path]["status"] = status
		data[project_path]["note"] = note
		data[project_path]["first_seen"] = stamp

	if not context.save():
		return 1

	print(f"added {len(added)} project{'s' if len(added) != 1 else ''}")

	tids = context.tids()

	for line in render_rows(
		[(project_path, data[project_path]) for project_path in added],
		settings,
		tids,
		show_headers=False,
		prefix="  ",
	):
		print(line)

	return 0


def command_init(context: Context, args: list[str]) -> int:
	settings = context.settings

	target = args[0] if args else os.getcwd()
	path = Path(os.path.expanduser(target)).resolve()

	if not path.is_dir():
		print(f"[ERROR] the path does not exist: {path}")
		return 1

	print(f"scanning {path}...")

	known = set(context.data)

	started = time.monotonic()

	find_projects(str(path), settings, context.data)

	added = [project_path for project_path in context.data if project_path not in known]
	updated = len(context.data) - len(known) - len(added)

	context.log(f"scan took {time.monotonic() - started:.2f}s")

	if not added:
		print(f"no new projects found ({len(context.data)} tracked)")

		if context.data:
			context.save()

		return 0

	stamp = time.strftime(settings["display"]["time_format"])

	for project_path in added:
		context.data[project_path]["first_seen"] = stamp

	if not context.save():
		return 1

	print(
		f"added {len(added)} project{'s' if len(added) != 1 else ''}, {len(context.data)} tracked"
	)

	if updated:
		print(f"refreshed {updated}")

	tids = context.tids()

	for line in render_rows(
		[(project_path, context.data[project_path]) for project_path in added],
		settings,
		tids,
		show_headers=False,
		prefix="  ",
	):
		print(line)

	return 0


def command_remove(context: Context, args: list[str]) -> int:
	if not args:
		print("[ERROR] remove requires a project")
		return 1

	settings = context.settings
	data = context.data

	if args[0].lower().strip("-") in ("all", "a", "*"):
		if not data:
			print("no projects to remove")
			return 0

		if not confirm(context, f"remove all {len(data)} tracked projects?"):
			print("cancelled")
			return 1

		count = len(data)
		data.clear()

		if not context.save():
			return 1

		print(f"removed {count} entries")

		return 0

	selected = select_projects(data, settings, args)

	if not selected:
		return 1

	tids = context.tids()

	if len(selected) > 1 and not confirm(context, f"remove {len(selected)} projects?"):
		print("cancelled")
		return 1

	lines = render_rows(selected.items(), settings, tids, show_headers=False, prefix="  ")

	for project_path in selected:
		del data[project_path]

	if not context.save():
		return 1

	if len(selected) == 1:
		print(f"removed {lines[0].strip()}")
	else:
		print(f"removed {len(selected)} projects")

		for line in lines:
			print(line)

	return 0


_EDIT_FIELDS = ("status", "note")


def command_edit(context: Context, args: list[str]) -> int:
	if not args:
		print("[ERROR] edit requires a project")
		return 1

	settings = context.settings

	selected = select_projects(context.data, settings, [args[0]])

	if not selected:
		return 1

	changes: dict[str, tuple[str, str]] = {}
	touched = 0
	index = 1

	while index < len(args):
		field_name = args[index].lower()

		if field_name not in _EDIT_FIELDS:
			print(
				f"[ERROR] unknown field '{args[index]}', expected one of: {', '.join(_EDIT_FIELDS)}"
			)
			return 1

		if index + 1 >= len(args):
			print(f"[ERROR] edit {field_name} requires a value")
			return 1

		if field_name == "note":
			value = " ".join(args[index + 1 :])
			index = len(args)
		else:
			value = args[index + 1]
			index += 2

		for project in selected.values():
			old = str(project.get(field_name, ""))

			if old != value:
				project[field_name] = value
				touched += 1

				if len(selected) == 1:
					changes[field_name] = (old, value)

	if len(selected) > 1:
		if not touched:
			print("nothing changed")
			return 0

		if not context.save():
			return 1

		print(f"edited {len(selected)} projects")

		return 0

	if not changes:
		print("nothing changed")
		return 0

	if not context.save():
		return 1

	path, project = next(iter(selected.items()))

	print(f"edited {format_project(path, project, settings, context.tids())}")

	empty = '""'

	for field_name, (old, new) in changes.items():
		print(f"  {field_name}: {C.GRAY}{old or empty}{C.RESET} -> {new or empty}")

	return 0


#
# Settings
#


def _display_settings(context: Context) -> None:
	settings = context.settings
	reference = defaults()

	print(f"{C.BOLD}{C.CYAN}Tracker settings{C.RESET}")
	print(f"{C.GRAY}{'-' * 70}{C.RESET}")
	print(f"{C.GRAY}source: {settings.path}{C.RESET}")

	for section, title in SECTION_TITLES.items():
		data = settings.raw.get(section)

		if not isinstance(data, dict):
			continue

		print(f"\n{C.BOLD}{title}{C.RESET}")

		for key, value in data.items():
			label = key.replace("_", " ").title()

			if isinstance(value, list):
				shown = ", ".join(str(item) for item in value) or "-"
			elif isinstance(value, dict):
				shown = f"{len(value)} entries"
			else:
				shown = str(value)

			changed = reference.get(section, {}).get(key, object()) != value
			marker = f" {C.GRAY}(changed){C.RESET}" if changed else ""

			print(f"  {label:<22} {C.YELLOW}{shown}{C.RESET}{marker}")

	for problem in settings.problems:
		print(f"\n{C.YELLOW}[WARNING] {problem}{C.RESET}")


def command_settings(context: Context, args: list[str]) -> int:
	settings = context.settings

	if not args:
		_display_settings(context)
		return 0

	action = args[0].lower().strip("-")

	if action in ("edit", "e"):
		settings.edit()
		return 0

	if action in ("path", "p", "where"):
		print(settings.path)
		return 0

	if action in ("get", "g"):
		if len(args) < 2:
			print("[ERROR] get requires a setting name")
			return 1

		for key in args[1:]:
			value = settings.get(key)

			if value is None:
				print(f"[ERROR] unknown setting '{key}'")
				return 1

			print(f"{key} = {value}")

		return 0

	if action in ("set", "s"):
		if len(args) < 3:
			print("[ERROR] set requires a setting name and a value")
			return 1

		key = args[1]
		raw = " ".join(args[2:])

		try:
			updated = settings.override(key, parse_setting_value(raw))
		except KeyError:
			print(f"[ERROR] unknown setting '{key}'")
			return 1
		except ValueError as error:
			print(f"[ERROR] {error}")
			return 1

		value = updated.get(key)

		error = write_setting(settings.path, key, value)

		if error:
			print(f"[ERROR] {error}")
			return 1

		print(f"{key} = {value}")
		print(f"{C.GRAY}saved to {settings.path}{C.RESET}")

		return 0

	print(f"[ERROR] unknown settings action '{args[0]}'")
	print("available: edit, path, get, set")

	return 1


#
# Daemon
#


def command_daemon(context: Context, args: list[str]) -> int:
	action = args[0].lower().strip("-") if args else "start"

	if action in ("kill", "k", "stop"):
		return daemon.stop()

	if action in ("status", "st", "state"):
		return daemon.status(context.settings)

	if action in ("log", "logs", "l"):
		lines = 40

		if len(args) > 1 and args[1].isdigit():
			lines = int(args[1])

		return daemon.show_log(lines)

	if action in ("run", "foreground", "fg"):
		return daemon.run(context.settings)

	if action in ("restart", "r"):
		daemon.stop()
		return daemon.start(context.settings)

	if action in ("start", "s"):
		return daemon.start(context.settings)

	if args:
		print(f"[ERROR] unknown daemon action '{args[0]}'")
		print("available: start, stop, restart, status, log, run")
		return 1

	return daemon.start(context.settings)
