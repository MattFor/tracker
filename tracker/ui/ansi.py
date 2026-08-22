import os
import sys

from typing import IO

_CODES = {
	"RESET": "\033[0m",
	"BOLD": "\033[1m",
	"DIM": "\033[2m",
	"RED": "\033[31m",
	"GREEN": "\033[32m",
	"YELLOW": "\033[33m",
	"BLUE": "\033[34m",
	"MAGENTA": "\033[35m",
	"CYAN": "\033[36m",
	"WHITE": "\033[37m",
	"GRAY": "\033[90m",
}


class Palette:
	RESET: str
	BOLD: str
	DIM: str
	RED: str
	GREEN: str
	YELLOW: str
	BLUE: str
	MAGENTA: str
	CYAN: str
	WHITE: str
	GRAY: str

	def __init__(self, enabled: bool = True) -> None:
		self.enabled = True
		self.set_enabled(enabled)

	def set_enabled(self, enabled: bool) -> None:
		self.enabled = enabled

		for name, code in _CODES.items():
			setattr(self, name, code if enabled else "")

	def paint(self, text: str, colour: str) -> str:
		if not self.enabled or not colour:
			return text

		code = _CODES.get(colour.strip().upper())

		if not code:
			return text

		return f"{code}{text}{self.RESET}"


C = Palette(True)


def configure(setting: bool = True, stream: IO[str] | None = None) -> None:
	stream = stream or sys.stdout

	if os.environ.get("FORCE_COLOR"):
		C.set_enabled(bool(setting))
		return

	if os.environ.get("NO_COLOR") is not None or os.environ.get("TERM") == "dumb":
		C.set_enabled(False)
		return

	try:
		interactive = stream.isatty()
	except (AttributeError, ValueError):
		interactive = False

	C.set_enabled(bool(setting) and interactive)
