import re

from datetime import datetime

_ANSI = re.compile(r"\033\[[0-9;]*m")
_WHITESPACE = re.compile(r"\s+")

_ELLIPSIS = "..."


def strip_ansi(text: str) -> str:
	return _ANSI.sub("", text)


def visible_length(text: str) -> int:
	return len(strip_ansi(text))


def pad(text: str, width: int) -> str:
	padding = width - visible_length(text)

	if padding <= 0:
		return text

	return text + " " * padding


def truncate(text: str, width: int) -> str:
	if width <= 0:
		return ""

	if len(text) <= width:
		return text

	if width <= len(_ELLIPSIS):
		return text[:width]

	return text[: width - len(_ELLIPSIS)] + _ELLIPSIS


def flatten(text: str) -> str:
	return _WHITESPACE.sub(" ", text.replace("\n", " . ")).strip()


def wrap(text: str, width: int) -> list[str]:
	if width <= 0:
		return [text] if text else []

	lines: list[str] = []

	for paragraph in text.splitlines() or [""]:
		words = paragraph.split()

		if not words:
			lines.append("")
			continue

		current = words[0]

		for word in words[1:]:
			if len(current) + 1 + len(word) <= width:
				current = f"{current} {word}"
			else:
				lines.append(current)
				current = word

		lines.append(current)

	return lines


def human_size(size: int) -> str:
	value = float(size)

	for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
		if value < 1024 or unit == "TiB":
			if unit == "B":
				return f"{int(value)} {unit}"

			return f"{value:.1f} {unit}"

		value /= 1024

	return f"{value:.1f} TiB"


def relative_time(moment: datetime, now: datetime | None = None) -> str:
	now = now or datetime.now()

	seconds = (now - moment).total_seconds()
	future = seconds < 0
	seconds = abs(seconds)

	steps = (
		(60.0, "second"),
		(60.0, "minute"),
		(24.0, "hour"),
		(7.0, "day"),
		(4.345, "week"),
		(12.0, "month"),
	)

	value = seconds
	unit = "second"

	for size, name in steps:
		if value < size:
			unit = name
			break

		value /= size
		unit = name

	else:
		unit = "year"

	amount = int(value)

	if unit == "second" and amount < 45:
		return "just now"

	plural = "" if amount == 1 else "s"

	return f"in {amount} {unit}{plural}" if future else f"{amount} {unit}{plural} ago"


def parse_time(value: str, time_format: str) -> datetime | None:
	if not value or value == "unknown":
		return None

	for candidate in (time_format, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
		try:
			return datetime.strptime(value, candidate)
		except (ValueError, TypeError):
			continue

	return None
