import sys

from typing import Any, Callable

from tracker.cli import commands
from tracker.cli.commands import Context
from tracker.config.settings import Settings
from tracker.core.storage import load_data
from tracker.ui import ansi
from tracker.ui.ansi import C
from tracker.ui.render import print_projects

Handler = Callable[[Context, list[str]], int]

COMMANDS: dict[str, str] = {
	"version": "version",
	"v": "version",
	"help": "help",
	"h": "help",
	"list": "list",
	"l": "list",
	"ls": "list",
	"add": "add",
	"a": "add",
	"remove": "remove",
	"rm": "remove",
	"r": "remove",
	"delete": "remove",
	"del": "remove",
	"check": "check",
	"c": "check",
	"cc": "check",
	"info": "check",
	"edit": "edit",
	"e": "edit",
	"init": "init",
	"i": "init",
	"scan": "init",
	"settings": "settings",
	"s": "settings",
	"config": "settings",
	"conf": "settings",
	"daemon": "daemon",
	"d": "daemon",
	"daemonize": "daemon",
	"daemonise": "daemon",
	"background": "daemon",
	"b": "daemon",
	"bg": "daemon",
	"path": "path",
	"p": "path",
	"where": "path",
	"stats": "stats",
	"stat": "stats",
	"summary": "stats",
}

HANDLERS: dict[str, Handler] = {
	"version": commands.command_version,
	"help": commands.command_help,
	"list": commands.command_list,
	"add": commands.command_add,
	"remove": commands.command_remove,
	"check": commands.command_check,
	"edit": commands.command_edit,
	"init": commands.command_init,
	"settings": commands.command_settings,
	"daemon": commands.command_daemon,
	"path": commands.command_path,
	"stats": commands.command_stats,
	"show": commands.command_show,
}

GREEDY = frozenset({"add", "edit"})

VERBOSE_FLAGS = frozenset({"verbose", "vv"})
YES_FLAGS = frozenset({"yes", "y", "force", "f"})
NO_COLOUR_FLAGS = frozenset({"no-color", "no-colour", "nocolor", "nocolour"})
COLOUR_FLAGS = frozenset({"color", "colour"})


def normalise(token: str) -> str:
	return token.lower().strip("-")


def command_of(token: str) -> str | None:
	return COMMANDS.get(normalise(token))


def split(args: list[str]) -> list[tuple[str, list[str]]]:
	segments: list[tuple[str, list[str]]] = []

	index = 0

	while index < len(args):
		name = command_of(args[index])

		if name is None:
			name = "show"
		else:
			index += 1

		if name in GREEDY:
			segments.append((name, args[index:]))
			break

		collected: list[str] = []

		while index < len(args) and command_of(args[index]) is None:
			collected.append(args[index])
			index += 1

		segments.append((name, collected))

	return segments


def extract_flags(args: list[str]) -> tuple[list[str], dict[str, Any]]:
	flags: dict[str, Any] = {"verbose": False, "yes": False, "colour": None}

	remaining: list[str] = []
	greedy_reached = False

	for token in args:
		if greedy_reached and not token.startswith("-"):
			remaining.append(token)
			continue

		if command_of(token) in GREEDY:
			greedy_reached = True

		key = normalise(token)

		if key in VERBOSE_FLAGS:
			flags["verbose"] = True
			continue

		if token.startswith("-") and key in YES_FLAGS:
			flags["yes"] = True
			continue

		if token.startswith("-") and key in NO_COLOUR_FLAGS:
			flags["colour"] = False
			continue

		if token.startswith("-") and key in COLOUR_FLAGS:
			flags["colour"] = True
			continue

		remaining.append(token)

	return remaining, flags


def main(argv: list[str] | None = None) -> int:
	args = list(sys.argv[1:] if argv is None else argv)

	args, flags = extract_flags(args)

	settings = Settings()

	colour = settings["output"]["colour"] if flags["colour"] is None else flags["colour"]
	ansi.configure(bool(colour))

	for problem in settings.problems:
		print(f"{C.YELLOW}[WARNING] {problem}{C.RESET}", file=sys.stderr)

	verbose = bool(flags["verbose"] or settings["logging"]["always_verbose"])

	context = Context(
		settings=settings,
		data=load_data(settings),
		verbose=verbose,
		assume_yes=bool(flags["yes"]),
	)

	context.log(f"settings: {settings.path}")
	context.log(f"projects: {len(context.data)}")

	if not args:
		print_projects(context.data, settings)
		return 0

	status = 0

	for name, arguments in split(args):
		handler = HANDLERS.get(name)

		if handler is None:
			print(f"[ERROR] unknown command '{name}'")
			status = 1
			continue

		try:
			status = handler(context, arguments) or status
		except KeyboardInterrupt:
			print()
			return 130
		except BrokenPipeError:
			return 0

	return status
