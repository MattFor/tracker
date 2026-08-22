from tests.helpers import SAMPLE, make_projects, make_settings

from tracker.core.models import get_id, new_project, normalise
from tracker.core.selection import (
	filter_projects,
	regex_projects,
	search_projects,
	select_projects,
	sort_projects,
	temporary_ids,
)


def sample():
	return make_projects(*SAMPLE)


def names(projects):
	return [path.rsplit("/", 1)[-1] for path in projects]


def test_ids_sort_numerically():
	projects = {}

	for number in (1, 2, 9, 10, 11):
		path = f"/code/project{number}"
		projects[path] = new_project(path, status="x", project_id=number)

	settings = make_settings(sorting__by="id", sorting__direction="ascending")

	ordered = [project["id"] for _, project in sort_projects(projects, settings)]

	assert ordered == [1, 2, 9, 10, 11]


def test_unknown_timestamps_sort_last_when_descending():
	projects = make_projects(
		("/code/a", "x", "2026-01-01 00:00:00", ""),
		("/code/b", "x", "unknown", ""),
	)

	settings = make_settings(sorting__by="last_touched", sorting__direction="descending")

	assert names(dict(sort_projects(projects, settings))) == ["a", "b"]


def test_temporary_ids_follow_the_sorted_view():
	settings = make_settings(sorting__by="name", sorting__direction="ascending")

	assert temporary_ids(sample(), settings) == {
		"/home/user/code/alpha": 1,
		"/home/user/code/beta": 2,
		"/home/user/code/gamma": 3,
	}


def test_select_by_name_and_path():
	settings = make_settings()

	assert names(select_projects(sample(), settings, ["beta"])) == ["beta"]
	assert names(select_projects(sample(), settings, ["/home/user/code/beta"])) == [
		"beta"
	]


def test_select_inclusive_range():
	settings = make_settings(sorting__by="name", sorting__direction="ascending")

	assert names(select_projects(sample(), settings, ["1-2"])) == ["alpha", "beta"]
	assert sorted(names(select_projects(sample(), settings, ["3-1"]))) == [
		"alpha",
		"beta",
		"gamma",
	]


def test_select_relative_range():
	settings = make_settings(sorting__by="name", sorting__direction="ascending")

	assert names(select_projects(sample(), settings, ["1+1"])) == ["alpha", "beta"]


def test_select_all():
	settings = make_settings()

	assert len(select_projects(sample(), settings, ["all"])) == 3


def test_out_of_range_numbers_are_ignored_not_fatal():
	settings = make_settings(sorting__by="name", sorting__direction="ascending")

	assert names(select_projects(sample(), settings, ["2-9"])) == ["beta", "gamma"]


def test_explicit_id_and_tid_prefixes():
	projects = sample()
	settings = make_settings(sorting__by="name", sorting__direction="descending")

	assert names(select_projects(projects, settings, ["@1"])) == ["gamma"]
	assert names(select_projects(projects, settings, ["#1"])) == ["alpha"]


def test_filters_include_and_exclude():
	projects = sample()

	assert names(filter_projects(projects, ["+m:beta"])) == ["beta"]
	assert names(filter_projects(projects, ["-m:beta"])) == ["alpha", "gamma"]
	assert names(filter_projects(projects, ["+r:^g"])) == ["gamma"]
	assert names(filter_projects(projects, ["-r:^g"])) == ["alpha", "beta"]


def test_invalid_filters_do_not_change_the_result():
	projects = sample()

	assert len(filter_projects(projects, ["nonsense"])) == 3
	assert len(filter_projects(projects, ["+z:beta"])) == 3
	assert len(filter_projects(projects, ["+r:[unclosed"])) == 3


def test_search_and_regex():
	projects = sample()

	assert names(search_projects(projects, "BET")) == ["beta"]
	assert names(regex_projects(projects, "a$")) == ["alpha", "beta", "gamma"]
	assert regex_projects(projects, "[unclosed") is None


def test_get_id_skips_used_numbers():
	projects = sample()

	assert get_id(projects) == 4
	assert get_id({}) == 1


def test_normalise_repairs_damaged_entries():
	repaired = normalise(
		{
			"/code/a": {"id": 1, "tid": 5},
			"/code/b": {"id": 1},
			"not a project": "junk",
		}
	)

	assert "tid" not in repaired["/code/a"]
	assert repaired["/code/a"]["status"] == "unknown"
	assert repaired["/code/b"]["id"] != repaired["/code/a"]["id"]
	assert "not a project" not in repaired
