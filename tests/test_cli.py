from tracker.cli.app import extract_flags, split


def test_a_bare_name_becomes_a_lookup():
	assert split(["tracker"]) == [("show", ["tracker"])]


def test_commands_can_be_chained():
	assert split(["list", "5", "version"]) == [("list", ["5"]), ("version", [])]


def test_free_text_commands_swallow_the_rest():
	assert split(["add", "~/code", "active", "a note with list in it"]) == [
		("add", ["~/code", "active", "a note with list in it"])
	]

	assert split(["edit", "3", "note", "check this remove that"]) == [
		("edit", ["3", "note", "check this remove that"])
	]


def test_dashed_aliases_are_accepted():
	assert split(["--list"]) == [("list", [])]
	assert split(["-h"]) == [("help", [])]


def test_check_and_settings_aliases_do_not_collide():
	assert split(["c"])[0][0] == "check"
	assert split(["cc"])[0][0] == "check"
	assert split(["s"])[0][0] == "settings"
	assert split(["config"])[0][0] == "settings"


def test_flags_are_pulled_out_from_anywhere():
	args, flags = extract_flags(["list", "--verbose", "5"])

	assert args == ["list", "5"]
	assert flags["verbose"] is True

	args, flags = extract_flags(["remove", "all", "-y"])

	assert args == ["remove", "all"]
	assert flags["yes"] is True

	args, flags = extract_flags(["list", "--no-colour"])

	assert flags["colour"] is False


def test_flags_inside_a_note_stay_in_the_note():
	args, flags = extract_flags(["edit", "3", "note", "yes", "verbose"])

	assert args == ["edit", "3", "note", "yes", "verbose"]
	assert flags["verbose"] is False
