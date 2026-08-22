# Tracker

Simple tracker that tracks the projects in your directories, their versions and allows you to track their
status/completion progress.

## Install

```sh
./install.sh
./install.sh --daemon
./install.sh --uninstall
```

Requires Python 3.11+.

## Commands

| Command    | Aliases           | What it does                                                         |
|------------|-------------------|----------------------------------------------------------------------|
| `list`     | `l`, `ls`         | List projects, with search, regex, filters and setting overrides     |
| `check`    | `c`, `cc`, `info` | Everything about a project: git state, size, language, version, note |
| `add`      | `a`               | Track a project, or scan a directory and track what is inside        |
| `remove`   | `rm`, `r`, `del`  | Stop tracking projects, nothing is deleted from disk                 |
| `edit`     | `e`               | Change a `status` or a `note`                                        |
| `init`     | `i`, `scan`       | Scan a directory and merge the result into the database              |
| `path`     | `p`, `where`      | Print a project's path, e.g. `cd "$(t path tracker)"`                |
| `stats`    | `summary`         | Totals, a breakdown by status, most and least recently touched       |
| `settings` | `s`, `config`     | Show, edit, get or set the configuration                             |
| `daemon`   | `d`, `bg`         | `start`, `stop`, `restart`, `status`, `log`, `run`                   |

### Selecting projects

Anything that takes a project accepts an ID, a TID from the current view, a name, a path, or a range:

```
t check 12       # ID or TID 12
t check #12      # force the permanent ID
t check @12      # force the temporary ID
t edit 3-7 status completed
t edit 5+3 status shelf
t edit all status archived
```

## Configuration

`settings.toml` is chosen by default. Use `my_settings.toml` for a custom configuration.

```sh
t settings                                  # show everything
t settings set display.list_limit 30        # rewrites that one line
t settings edit                             # open in $EDITOR
t list sorting.by=name output.compact=true  # override for one command only
```

## Roadmap

- [x] daemon that keeps the database up to date on its own
- [x] proper folder structure and names
- [x] a partial or malformed `my_settings.toml` no longer breaks everything
- [x] show project versions inferred from the language config file (`pyproject.toml`, `Cargo.toml`, `package.json`, ...)
- [ ] make a release and mention the codeberg mirror
- [ ] possible zoxide integration for conflicting matches

## By MattFor
