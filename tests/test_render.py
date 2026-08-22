from tests.helpers import SAMPLE, make_projects, make_settings

from tracker.core.selection import temporary_ids
from tracker.ui import ansi
from tracker.ui.render import render_rows
from tracker.util.text import human_size, relative_time, truncate, wrap

ansi.C.set_enabled(False)


def sample():
	return make_projects(*SAMPLE)


def rows(width, **overrides):
	settings = make_settings(
		sorting__by="name",
		sorting__direction="ascending",
		display__columns=["tid", "name", "status"],
		display__vertical_separator=" | ",
		**overrides,
	)

	projects = sample()

	return render_rows(
		sorted(projects.items()),
		settings,
		temporary_ids(projects, settings),
		width=width,
	)


def test_short_note_shares_the_project_line():
	lines = rows(120)

	alpha = [line for line in lines if "alpha" in line][0]

	assert "short note" in alpha


def test_note_moves_below_when_the_terminal_is_narrow():
	lines = rows(40)

	index = next(i for i, line in enumerate(lines) if "alpha" in line)

	assert "short note" not in lines[index]
	assert "short note" in lines[index + 1]


def test_long_note_moves_below_and_wraps():
	lines = rows(80)

	index = next(i for i, line in enumerate(lines) if "gamma" in line)

	assert "much longer note" not in lines[index]
	assert "much longer note" in lines[index + 1]
	assert all(len(line) <= 80 for line in lines)


def test_note_column_header_appears_only_with_inline_notes():
	assert "NOTE" in rows(120)[0]
	assert "NOTE" not in rows(40)[0]


def test_below_position_never_shares_the_line():
	lines = rows(200, display__note_position="below")

	alpha = next(i for i, line in enumerate(lines) if "alpha" in line)

	assert "short note" not in lines[alpha]
	assert "short note" in lines[alpha + 1]


def test_inline_position_shortens_instead_of_wrapping():
	lines = rows(90, display__note_position="inline")

	gamma = next(line for line in lines if "gamma" in line)

	assert "..." in gamma
	assert len(gamma) <= 90


def test_notes_can_be_switched_off():
	lines = rows(200, display__show_notes=False)

	assert not any("short note" in line for line in lines)


def test_columns_shrink_before_the_line_overflows():
	settings = make_settings(
		display__columns=["name", "path"],
		display__show_headers=False,
		display__show_notes=False,
	)

	projects = sample()

	lines = render_rows(sorted(projects.items()), settings, width=40)

	assert all(len(line) <= 40 for line in lines)


def test_no_rows_renders_nothing():
	assert render_rows([], make_settings()) == []


def test_multi_line_notes_are_flattened_when_inline():
	projects = make_projects(
		("/code/a", "x", "2026-01-01 00:00:00", "line one\nline two")
	)

	settings = make_settings(display__columns=["name"], display__show_headers=False)

	lines = render_rows(sorted(projects.items()), settings, width=120)

	assert len(lines) == 1
	assert "line one" in lines[0] and "line two" in lines[0]


def test_text_helpers():
	assert truncate("abcdefgh", 5) == "ab..."
	assert truncate("abc", 5) == "abc"
	assert wrap("a bb ccc", 4) == ["a bb", "ccc"]
	assert human_size(2048) == "2.0 KiB"
	assert "ago" in relative_time(__import__("datetime").datetime(2020, 1, 1))
