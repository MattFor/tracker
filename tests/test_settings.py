import tomllib

from tests.helpers import make_settings

from tracker.config.settings import Settings, coerce, parse_setting_value
from tracker.config.defaults import defaults
from tracker.config.writer import serialise, write_setting


def test_partial_configuration_falls_back_to_defaults():
	settings = Settings.merged({"display": {"list_limit": 3}})

	assert settings["display"]["list_limit"] == 3
	assert settings["display"]["note_position"] == "auto"
	assert settings["sorting"]["by"] == defaults()["sorting"]["by"]


def test_empty_configuration_is_complete():
	settings = Settings.merged({})

	for key, _ in defaults().items():
		assert key in settings.raw


def test_unknown_keys_are_reported():
	settings = Settings.merged({"display": {"nonsense": 1}})

	assert any("nonsense" in problem for problem in settings.problems)


def test_override_rejects_the_wrong_type():
	settings = make_settings()

	try:
		settings.override("display.list_limit", "abc")
	except ValueError:
		pass
	else:
		raise AssertionError("a non numeric limit should be rejected")


def test_override_rejects_unknown_settings():
	settings = make_settings()

	try:
		settings.override("display.nope", 1)
	except KeyError:
		pass
	else:
		raise AssertionError("an unknown setting should be rejected")


def test_override_limits_choices():
	settings = make_settings()

	assert settings.override("sorting.by", "name")["sorting"]["by"] == "name"

	try:
		settings.override("sorting.by", "sideways")
	except ValueError:
		pass
	else:
		raise AssertionError("an unknown sort key should be rejected")


def test_coerce_accepts_comma_separated_lists():
	assert coerce("display.columns", "id,name", ["a"]) == ["id", "name"]


def test_parse_setting_value_uses_toml_rules():
	assert parse_setting_value("true") is True
	assert parse_setting_value("12") == 12
	assert parse_setting_value("plain") == "plain"


def test_writer_keeps_comments(tmp_path):
	path = tmp_path / "settings.toml"
	path.write_text("[display]\n# keep me\nlist_limit = 20\n")

	assert write_setting(path, "display.list_limit", 42) is None

	text = path.read_text()

	assert "# keep me" in text
	assert tomllib.loads(text)["display"]["list_limit"] == 42


def test_writer_adds_missing_keys_and_sections(tmp_path):
	path = tmp_path / "settings.toml"
	path.write_text("[display]\nlist_limit = 20\n")

	assert write_setting(path, "display.show_notes", False) is None
	assert write_setting(path, "daemon.interval", 30) is None

	data = tomllib.loads(path.read_text())

	assert data["display"]["show_notes"] is False
	assert data["daemon"]["interval"] == 30


def test_writer_replaces_multi_line_arrays(tmp_path):
	path = tmp_path / "settings.toml"
	path.write_text(
		'[projects]\nignore = [\n    ".git",\n    "venv"\n]\n\n[output]\ncolour = true\n'
	)

	assert write_setting(path, "projects.ignore", [".git"]) is None

	data = tomllib.loads(path.read_text())

	assert data["projects"]["ignore"] == [".git"]
	assert data["output"]["colour"] is True


def test_serialise_round_trips():
	assert serialise(True) == "true"
	assert serialise(7) == "7"
	assert serialise(["a", "b"]) == '["a", "b"]'
	assert serialise('say "hi"') == '"say \\"hi\\""'
