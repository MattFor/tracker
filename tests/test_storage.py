import os

from pathlib import Path

from tests.helpers import SAMPLE, make_projects, make_settings

from tracker.core.discovery import find_projects, get_last_touched_date
from tracker.core.storage import load_data, save_data
from tracker.util.files import load_pkl, save_pkl


def with_data_file(path: Path):
	os.environ["TRACKER_DATA"] = str(path)


def test_save_and_load_round_trip(tmp_path):
	with_data_file(tmp_path / "data.pkl")

	projects = make_projects(*SAMPLE)

	assert save_data(projects, make_settings())

	loaded = load_data(make_settings())

	assert set(loaded) == set(projects)
	assert loaded["/home/user/code/alpha"]["status"] == "current"


def test_temporary_ids_are_never_written(tmp_path):
	with_data_file(tmp_path / "data.pkl")

	projects = make_projects(*SAMPLE)
	projects["/home/user/code/alpha"]["tid"] = 7

	save_data(projects, make_settings())

	stored, _ = load_pkl(tmp_path / "data.pkl")

	assert "tid" not in stored["/home/user/code/alpha"]


def test_a_missing_database_is_simply_empty(tmp_path):
	with_data_file(tmp_path / "absent.pkl")

	assert load_data(make_settings()) == {}


def test_a_broken_database_is_moved_aside(tmp_path):
	path = tmp_path / "data.pkl"
	path.write_bytes(b"this is not a pickle")

	with_data_file(path)

	assert load_data(make_settings()) == {}
	assert not path.exists()
	assert list(tmp_path.glob("data.pkl.corrupt-*"))


def test_writes_are_atomic(tmp_path):
	path = tmp_path / "data.pkl"

	save_pkl(path, {"a": 1})

	assert [entry.name for entry in tmp_path.iterdir()] == ["data.pkl"]


def build_tree(root: Path) -> None:
	for name in ("alpha", "beta"):
		project = root / name
		(project / ".git").mkdir(parents=True)
		(project / "main.py").write_text("print()\n")

	nested = root / "beta" / "inner"
	(nested / ".git").mkdir(parents=True)

	plain = root / "not-a-project"
	plain.mkdir()
	(plain / "file.txt").write_text("x")


def test_find_projects_detects_git_directories(tmp_path):
	build_tree(tmp_path)

	found = find_projects(str(tmp_path), make_settings())

	assert set(Path(path).name for path in found) == {"alpha", "beta"}


def test_find_projects_can_descend_into_projects(tmp_path):
	build_tree(tmp_path)

	settings = make_settings(scan__stop_at_project=False)

	found = find_projects(str(tmp_path), settings)

	assert "inner" in {Path(path).name for path in found}


def test_find_projects_keeps_existing_entries(tmp_path):
	build_tree(tmp_path)

	settings = make_settings()

	found = find_projects(str(tmp_path), settings)

	alpha = str(tmp_path / "alpha")
	found[alpha]["status"] = "current"
	found[alpha]["note"] = "keep me"

	again = find_projects(str(tmp_path), settings, found)

	assert again[alpha]["status"] == "current"
	assert again[alpha]["note"] == "keep me"


def test_last_touched_survives_a_broken_symlink(tmp_path):
	(tmp_path / "real.txt").write_text("x")
	(tmp_path / "broken").symlink_to(tmp_path / "missing.txt")

	assert get_last_touched_date(str(tmp_path)) is not None


def test_last_touched_skips_ignored_directories(tmp_path):
	old = tmp_path / "src"
	old.mkdir()
	(old / "a.py").write_text("x")
	os.utime(old / "a.py", (1_000_000, 1_000_000))

	noisy = tmp_path / "node_modules"
	noisy.mkdir()
	(noisy / "b.js").write_text("x")

	skipped = get_last_touched_date(str(tmp_path), ["node_modules"])
	included = get_last_touched_date(str(tmp_path))

	assert skipped is not None and included is not None
	assert skipped < included
