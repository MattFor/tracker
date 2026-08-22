from typing import Any

COLUMNS = ("tid", "id", "name", "path", "status", "last_touched", "version", "language")

SORT_KEYS = ("id", "name", "path", "status", "last_touched", "time")
SORT_DIRECTIONS = ("ascending", "descending")

NOTE_POSITIONS = ("auto", "inline", "below")

CONFLICT_PREFERENCES = ("starts_with", "first_match")


def defaults() -> dict[str, Any]:
	return {
		"display": {
			"list_limit": 20,
			"show_headers": True,
			"show_notes": True,
			"note_position": "auto",
			"note_min_width": 24,
			"columns": ["tid", "id", "name", "status", "last_touched"],
			"time_format": "%Y-%m-%d %H:%M:%S",
			"relative_times": False,
			"vertical_separator": " | ",
			"horizontal_separator": "-",
			"max_width": 0,
			"filter": [],
			"status_colours": {
				"current": "green",
				"active": "green",
				"todo": "yellow",
				"planned": "yellow",
				"review-needed": "magenta",
				"blocked": "red",
				"shelf": "blue",
				"paused": "blue",
				"done": "cyan",
				"completed": "cyan",
				"final": "cyan",
				"maintenance": "cyan",
				"archived": "gray",
				"deleted": "gray",
				"unknown": "gray",
			},
		},
		"sorting": {
			"by": "last_touched",
			"direction": "descending",
		},
		"projects": {
			"default_status": "unknown",
			"ignore": [
				".git",
				".venv",
				"venv",
				"dist",
				"build",
				"target",
				"__pycache__",
				"node_modules",
			],
			"conflict_resolution_preference": "starts_with",
			"confirm_destructive": True,
		},
		"scan": {
			"detect_git": True,
			"recursive": True,
			"stop_at_project": True,
			"follow_symlinks": False,
			"timestamps_skip_ignored": True,
		},
		"output": {
			"colour": True,
			"compact": False,
			"absolute_paths": True,
		},
		"database": {
			"file": "data.pkl",
		},
		"logging": {
			"always_verbose": False,
		},
		"daemon": {
			"paths": [],
			"archive": True,
			"interval": 60,
			"timestamp_format": "%Y-%m-%d %H:%M:%S",
		},
	}


SECTION_TITLES = {
	"display": "Display",
	"sorting": "Sorting",
	"projects": "Projects",
	"scan": "Scanning",
	"output": "Output",
	"database": "Database",
	"logging": "Logging",
	"daemon": "Daemon",
}

CHOICES: dict[str, tuple[str, ...]] = {
	"display.note_position": NOTE_POSITIONS,
	"sorting.by": SORT_KEYS,
	"sorting.direction": SORT_DIRECTIONS,
	"projects.conflict_resolution_preference": CONFLICT_PREFERENCES,
}

OPEN_TABLES = frozenset({"display.status_colours"})
