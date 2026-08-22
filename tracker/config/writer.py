import re

from typing import Any
from pathlib import Path


def serialise(value: Any) -> str:
	if isinstance(value, bool):
		return "true" if value else "false"

	if isinstance(value, (int, float)):
		return str(value)

	if isinstance(value, list):
		return "[" + ", ".join(serialise(item) for item in value) + "]"

	text = str(value)
	escaped = text.replace("\\", "\\\\").replace('"', '\\"')

	return f'"{escaped}"'


def _section_bounds(lines: list[str], section: str) -> tuple[int, int] | None:
	header = re.compile(rf"^\s*\[\s*{re.escape(section)}\s*\]\s*$")

	start = None

	for index, line in enumerate(lines):
		if start is None:
			if header.match(line):
				start = index + 1

			continue

		if re.match(r"^\s*\[", line):
			return start, index

	if start is None:
		return None

	return start, len(lines)


def _value_span(
	lines: list[str], start: int, end: int, key: str
) -> tuple[int, int] | None:
	assignment = re.compile(rf"^\s*{re.escape(key)}\s*=")

	for index in range(start, end):
		if not assignment.match(lines[index]):
			continue

		depth = lines[index].count("[") - lines[index].count("]")
		last = index

		while depth > 0 and last + 1 < end:
			last += 1
			depth += lines[last].count("[") - lines[last].count("]")

		return index, last + 1

	return None


def write_setting(path: Path, dotted: str, value: Any) -> str | None:
	parts = dotted.split(".")

	if len(parts) != 2:
		return f"'{dotted}' cannot be edited automatically, use `settings edit`"

	section, key = parts

	try:
		text = path.read_text(encoding="utf-8")
	except OSError as error:
		return f"could not read {path}: {error}"

	lines = text.splitlines()
	replacement = f"{key} = {serialise(value)}"

	bounds = _section_bounds(lines, section)

	if bounds is None:
		lines.extend(["", f"[{section}]", replacement])
	else:
		start, end = bounds
		span = _value_span(lines, start, end, key)

		if span is None:
			insert = end

			while insert > start and not lines[insert - 1].strip():
				insert -= 1

			lines.insert(insert, replacement)
		else:
			lines[span[0] : span[1]] = [replacement]

	try:
		path.write_text("\n".join(lines) + "\n", encoding="utf-8")
	except OSError as error:
		return f"could not write {path}: {error}"

	return None
