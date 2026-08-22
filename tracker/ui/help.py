from tracker.ui.ansi import C

from tracker.config import paths
from tracker.config.metadata import PyProject


def print_help(project: PyProject) -> None:
	try:
		text = paths.HELP_FILE.read_text(encoding="utf-8")
	except OSError as error:
		print(f"[ERROR] could not read the help file: {error}")
		print(f"it should live at {paths.HELP_FILE}")
		return

	replacements = {
		"PROJECT_NAME": project.name.capitalize(),
		"PROJECT_VERSION": project.version,
		"PROJECT_AUTHOR": project.author,
		"BOLD": C.BOLD,
		"DIM": C.DIM,
		"RED": C.RED,
		"CYAN": C.CYAN,
		"GRAY": C.GRAY,
		"BLUE": C.BLUE,
		"GREEN": C.GREEN,
		"WHITE": C.WHITE,
		"YELLOW": C.YELLOW,
		"MAGENTA": C.MAGENTA,
		"RESET": C.RESET,
	}

	for key, value in replacements.items():
		text = text.replace(f"{{{key}}}", str(value))

	print(text)
