import os
import sys
import copy
import time
import errno
import signal
import subprocess

from pathlib import Path

from tracker.config import paths
from tracker.config.settings import Settings, settings as default_settings
from tracker.core.discovery import find_projects
from tracker.core.models import Projects, get_id
from tracker.core.storage import load_data, save_data

DELETED_MARKER = "[DELETED]"


#
# Process control
#


def read_pid() -> int | None:
	pid_file = paths.daemon_pid_file()

	try:
		pid = int(pid_file.read_text(encoding="utf-8").strip())
	except (OSError, ValueError):
		return None

	if not is_running(pid):
		try:
			pid_file.unlink(missing_ok=True)
		except OSError:
			pass

		return None

	return pid


def is_running(pid: int) -> bool:
	try:
		os.kill(pid, 0)
	except ProcessLookupError:
		return False
	except PermissionError:
		return True
	except OSError as error:
		return error.errno != errno.ESRCH

	return True


def write_pid(pid: int) -> None:
	pid_file = paths.daemon_pid_file()

	try:
		pid_file.parent.mkdir(parents=True, exist_ok=True)
		pid_file.write_text(f"{pid}\n", encoding="utf-8")
	except OSError as error:
		print(f"[ERROR] could not write the pid file: {error}")


def find_stray_daemons() -> list[int]:
	try:
		result = subprocess.run(
			["pgrep", "-f", r"python.*-m (tracker daemon run|src\.daemon)"],
			capture_output=True,
			text=True,
		)
	except (OSError, subprocess.SubprocessError):
		return []

	if result.returncode != 0:
		return []

	pids = []

	for line in result.stdout.splitlines():
		try:
			pid = int(line.strip())
		except ValueError:
			continue

		if pid not in (os.getpid(), os.getppid()):
			pids.append(pid)

	return pids


def start(settings: Settings | None = None) -> int:
	settings = settings or default_settings

	running = read_pid()

	if running is not None:
		print(f"the daemon is already running (pid {running})")
		return 0

	if not settings["daemon"]["paths"]:
		print("[ERROR] no daemon paths configured")
		print("add them under [daemon] in " + str(settings.path))
		return 1

	log_file = paths.daemon_log_file()

	try:
		log_file.parent.mkdir(parents=True, exist_ok=True)
		log = open(log_file, "a", buffering=1, encoding="utf-8")
	except OSError as error:
		print(f"[ERROR] could not open the log file: {error}")
		return 1

	try:
		with log:
			process = subprocess.Popen(
				[sys.executable, "-u", "-m", "tracker", "daemon", "run"],
				cwd=str(paths.PROJECT_ROOT),
				stdin=subprocess.DEVNULL,
				stdout=log,
				stderr=subprocess.STDOUT,
				start_new_session=True,
			)
	except OSError as error:
		print(f"[ERROR] could not start the daemon: {error}")
		return 1

	write_pid(process.pid)

	print(f"daemon started (pid {process.pid})")
	print(f"logging to {log_file}")

	return 0


def stop() -> int:
	pids = []

	pid = read_pid()

	if pid is not None:
		pids.append(pid)

	pids.extend(stray for stray in find_stray_daemons() if stray not in pids)

	if not pids:
		print("no daemons running")
		return 0

	stopped = 0

	for pid in pids:
		try:
			os.kill(pid, signal.SIGTERM)
			stopped += 1
		except ProcessLookupError:
			continue
		except PermissionError:
			print(f"[ERROR] not allowed to stop daemon {pid}")

	try:
		paths.daemon_pid_file().unlink(missing_ok=True)
	except OSError:
		pass

	if not stopped:
		print("no daemons running")
		return 0

	print(f"stopped {stopped} daemon{'s' if stopped != 1 else ''}")

	return 0


def status(settings: Settings | None = None) -> int:
	settings = settings or default_settings

	pid = read_pid()

	if pid is None:
		print("daemon: not running")
	else:
		print(f"daemon: running (pid {pid})")

	print(f"log:      {paths.daemon_log_file()}")
	print(f"pid file: {paths.daemon_pid_file()}")
	print(f"interval: {settings['daemon']['interval']}s")

	watched = settings["daemon"]["paths"]

	print("watching:" if watched else "watching: nothing configured")

	for path in watched:
		print(f"  {os.path.abspath(os.path.expanduser(path))}")

	return 0


def show_log(lines: int = 40) -> int:
	log_file = paths.daemon_log_file()

	if not log_file.is_file():
		print(f"no log yet at {log_file}")
		return 0

	try:
		content = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
	except OSError as error:
		print(f"[ERROR] could not read the log: {error}")
		return 1

	for line in content[-lines:]:
		print(line)

	return 0


#
# Scanning
#


def _archive(project: dict, timestamp: str) -> None:
	original = str(project.get("note", "") or "")

	project["archived"] = True
	project["deleted_at"] = timestamp
	project["archived_note"] = original

	statistics = [
		f"{DELETED_MARKER} ({timestamp})",
		f"ID: {project.get('id', '-')}",
		f"Last touched: {project.get('last_touched', 'unknown')}",
	]

	first_seen = project.get("first_seen")

	if first_seen:
		statistics.append(f"First seen: {first_seen}")

	if original:
		statistics.append(original)

	project["note"] = "\n".join(statistics)


def _restore(project: dict) -> None:
	project["archived"] = False
	project["note"] = str(project.get("archived_note", "") or "")

	project.pop("archived_note", None)
	project.pop("deleted_at", None)


def update_database(
	watched: list[str],
	data: Projects,
	archive: bool,
	settings: Settings | None = None,
) -> tuple[Projects, bool, list[str], list[str]]:
	settings = settings or default_settings

	before = copy.deepcopy(data)
	before_paths = set(data)

	timestamp_format: str = settings["daemon"]["timestamp_format"]

	valid: list[Path] = []
	found: set[str] = set()

	for entry in watched:
		path = Path(os.path.expanduser(entry)).resolve()

		if not path.is_dir():
			print(f"[ERROR] daemon path is not a directory: {path}")
			continue

		valid.append(path)

		scanned = find_projects(str(path), settings)
		found.update(scanned)

		for project_path, scanned_project in scanned.items():
			existing = data.get(project_path)

			if existing is None:
				scanned_project["id"] = get_id(data)
				scanned_project["first_seen"] = time.strftime(timestamp_format)
				scanned_project["archived"] = False

				data[project_path] = scanned_project
				continue

			existing["last_touched"] = scanned_project["last_touched"]

			if existing.get("archived", False):
				_restore(existing)

	removed: list[str] = []

	for project_path in list(data):
		project = Path(project_path)

		if not any(project.is_relative_to(root) for root in valid):
			continue

		if project_path in found:
			continue

		project_data = data[project_path]

		if not archive:
			removed.append(project_path)
			del data[project_path]
			continue

		if project_data.get("archived", False):
			continue

		_archive(project_data, time.strftime(timestamp_format))
		removed.append(project_path)

	added = [path for path in data if path not in before_paths]

	changed = data != before

	if changed:
		save_data(data, settings)

	return data, changed, added, removed


def _report(title: str, entries: list[tuple[str, str, str]], timestamp: str) -> None:
	if not entries:
		return

	marker_width = max(len(marker) for marker, _, _ in entries)
	name_width = max(len(name) for _, name, _ in entries)

	print(f"[{timestamp}] {title}:")

	for marker, name, path in entries:
		print(f"  {marker:<{marker_width}}  {name:<{name_width}}  {path}")


def run(settings: Settings | None = None) -> int:
	settings = settings or default_settings

	archive: bool = settings["daemon"]["archive"]
	interval: int = settings["daemon"]["interval"]
	watched: list[str] = settings["daemon"]["paths"]
	timestamp_format: str = settings["daemon"]["timestamp_format"]

	if not watched:
		print("[ERROR] no daemon paths configured")
		print(f"add them under [daemon] in {settings.path}")
		return 1

	if not isinstance(interval, int) or interval < 1:
		interval = 60

	watched = [os.path.abspath(os.path.expanduser(path)) for path in watched]

	data = load_data(settings)

	write_pid(os.getpid())

	stopping = False

	def request_stop(*_: object) -> None:
		nonlocal stopping
		stopping = True

	signal.signal(signal.SIGTERM, request_stop)
	signal.signal(signal.SIGINT, request_stop)

	print(f"[{time.strftime(timestamp_format)}] daemon started (pid {os.getpid()})")
	print("watching:")

	for path in watched:
		print(f"  {path}")

	print(f"scan interval: {interval}s")

	try:
		while not stopping:
			started = time.monotonic()

			data, changed, added, removed = update_database(
				watched, data, archive, settings
			)

			timestamp = time.strftime(timestamp_format)

			_report(
				f"added {len(added)} project{'s' if len(added) != 1 else ''}",
				[(str(data[path]["id"]), Path(path).name, path) for path in added],
				timestamp,
			)

			_report(
				f"removed {len(removed)} project{'s' if len(removed) != 1 else ''}",
				[("-", Path(path).name, path) for path in removed],
				timestamp,
			)

			if not added and not removed and changed:
				print(f"[{timestamp}] database updated")

			elapsed = time.monotonic() - started
			remaining = max(0.0, interval - elapsed)

			while remaining > 0 and not stopping:
				nap = min(1.0, remaining)
				time.sleep(nap)
				remaining -= nap

	except KeyboardInterrupt:
		pass

	finally:
		try:
			if read_pid() == os.getpid():
				paths.daemon_pid_file().unlink(missing_ok=True)
		except OSError:
			pass

	print(f"[{time.strftime(timestamp_format)}] daemon stopped")

	return 0


if __name__ == "__main__":
	sys.exit(run())
