import os
import re
import json
import shutil
import subprocess

from pathlib import Path
from typing import Iterable
from datetime import datetime
from functools import lru_cache
from dataclasses import dataclass, field

from tracker.util.files import load_toml

GIT_TIMEOUT = 5


#
# Git
#


@dataclass
class GitInfo:
	branch: str = ""
	remote: str = ""
	commit: str = ""
	subject: str = ""
	committed: datetime | None = None
	commits: int = 0
	modified: int = 0
	untracked: int = 0
	staged: int = 0
	detached: bool = False

	@property
	def clean(self) -> bool:
		return not (self.modified or self.untracked or self.staged)


def _git(path: str, *arguments: str) -> str | None:
	try:
		result = subprocess.run(
			["git", "--no-optional-locks", "-C", path, *arguments],
			capture_output=True,
			text=True,
			timeout=GIT_TIMEOUT,
		)
	except (OSError, subprocess.SubprocessError):
		return None

	if result.returncode != 0:
		return None

	return result.stdout.strip()


@lru_cache(maxsize=256)
def git_info(path: str) -> GitInfo | None:
	if not shutil.which("git") or not os.path.isdir(path):
		return None

	if _git(path, "rev-parse", "--is-inside-work-tree") != "true":
		return None

	info = GitInfo()

	branch = _git(path, "branch", "--show-current") or ""

	if not branch:
		branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD") or ""

	if branch == "HEAD":
		info.detached = True
		branch = _git(path, "rev-parse", "--short", "HEAD") or "detached"

	info.branch = branch

	info.remote = _git(path, "remote", "get-url", "origin") or ""

	last = _git(path, "log", "-1", "--format=%h%x1f%s%x1f%cI")

	if last:
		parts = last.split("\x1f")

		if len(parts) == 3:
			info.commit, info.subject, stamp = parts

			try:
				info.committed = datetime.fromisoformat(stamp).replace(tzinfo=None)
			except ValueError:
				info.committed = None

	count = _git(path, "rev-list", "--count", "HEAD")

	if count and count.isdigit():
		info.commits = int(count)

	status = _git(path, "status", "--porcelain")

	if status:
		for line in status.splitlines():
			if line.startswith("??"):
				info.untracked += 1
				continue

			if line[:1].strip():
				info.staged += 1

			if line[1:2].strip():
				info.modified += 1

	return info


#
# Manifests
#


@dataclass
class Manifest:
	language: str
	source: str
	name: str = ""
	version: str = ""


def _read(path: Path, limit: int = 200_000) -> str:
	try:
		return path.read_text(encoding="utf-8", errors="replace")[:limit]
	except OSError:
		return ""


def _search(path: Path, pattern: str) -> str:
	match = re.search(pattern, _read(path), re.MULTILINE)

	return match.group(1).strip() if match else ""


def _python(root: Path) -> Manifest | None:
	pyproject = root / "pyproject.toml"

	if pyproject.is_file():
		data = load_toml(pyproject) or {}

		project = data.get("project") if isinstance(data.get("project"), dict) else {}
		poetry = (
			data.get("tool", {}).get("poetry", {})
			if isinstance(data.get("tool"), dict)
			else {}
		)

		if not isinstance(poetry, dict):
			poetry = {}

		return Manifest(
			language="Python",
			source="pyproject.toml",
			name=str(project.get("name") or poetry.get("name") or ""),
			version=str(project.get("version") or poetry.get("version") or ""),
		)

	for candidate, pattern in (
		("setup.py", r"version\s*=\s*[\"']([^\"']+)[\"']"),
		("setup.cfg", r"^version\s*=\s*(.+)$"),
	):
		path = root / candidate

		if path.is_file():
			return Manifest("Python", candidate, version=_search(path, pattern))

	if (root / "requirements.txt").is_file():
		return Manifest("Python", "requirements.txt")

	return None


def _javascript(root: Path) -> Manifest | None:
	package = root / "package.json"

	if not package.is_file():
		return None

	language = "TypeScript" if (root / "tsconfig.json").is_file() else "JavaScript"

	try:
		data = json.loads(_read(package))
	except (json.JSONDecodeError, ValueError):
		data = {}

	if not isinstance(data, dict):
		data = {}

	return Manifest(
		language=language,
		source="package.json",
		name=str(data.get("name") or ""),
		version=str(data.get("version") or ""),
	)


def _rust(root: Path) -> Manifest | None:
	cargo = root / "Cargo.toml"

	if not cargo.is_file():
		return None

	data = load_toml(cargo) or {}
	package = data.get("package") if isinstance(data.get("package"), dict) else {}

	return Manifest(
		language="Rust",
		source="Cargo.toml",
		name=str(package.get("name") or ""),
		version=str(package.get("version") or ""),
	)


_SIMPLE: tuple[tuple[str, str, str], ...] = (
	("go.mod", "Go", r"^module\s+(\S+)"),
	("composer.json", "PHP", r"\"version\"\s*:\s*\"([^\"]+)\""),
	("pubspec.yaml", "Dart", r"^version:\s*(\S+)"),
	("mix.exs", "Elixir", r"version:\s*\"([^\"]+)\""),
	("pom.xml", "Java", r"<version>([^<]+)</version>"),
	("build.gradle", "Java", r"^version\s*=?\s*[\"']([^\"']+)[\"']"),
	("build.gradle.kts", "Kotlin", r"^version\s*=\s*[\"']([^\"']+)[\"']"),
	("CMakeLists.txt", "C/C++", r"project\s*\([^)]*VERSION\s+([0-9][^\s)]*)"),
	("Gemfile", "Ruby", r"^ruby\s+[\"']([^\"']+)[\"']"),
	("deno.json", "TypeScript", r"\"version\"\s*:\s*\"([^\"]+)\""),
	("Package.swift", "Swift", ""),
	("Makefile", "Make", ""),
)


@lru_cache(maxsize=512)
def detect_manifest(path: str) -> Manifest | None:
	root = Path(path)

	if not root.is_dir():
		return None

	for detector in (_python, _javascript, _rust):
		manifest = detector(root)

		if manifest is not None:
			return manifest

	for filename, language, pattern in _SIMPLE:
		candidate = root / filename

		if candidate.is_file():
			version = _search(candidate, pattern) if pattern else ""

			if filename == "go.mod":
				return Manifest(language, filename, name=version)

			return Manifest(language, filename, version=version)

	for candidate in root.glob("*.csproj"):
		return Manifest(
			"C#",
			candidate.name,
			version=_search(candidate, r"<Version>([^<]+)</Version>"),
		)

	for candidate in root.glob("*.gemspec"):
		return Manifest(
			"Ruby",
			candidate.name,
			version=_search(candidate, r"version\s*=\s*[\"']([^\"']+)[\"']"),
		)

	return None


#
# Disk usage
#


_LANGUAGE_BY_EXTENSION = {
	".py": "Python",
	".rs": "Rust",
	".go": "Go",
	".js": "JavaScript",
	".mjs": "JavaScript",
	".ts": "TypeScript",
	".tsx": "TypeScript",
	".jsx": "JavaScript",
	".c": "C",
	".h": "C",
	".cpp": "C++",
	".cc": "C++",
	".hpp": "C++",
	".cs": "C#",
	".java": "Java",
	".kt": "Kotlin",
	".rb": "Ruby",
	".php": "PHP",
	".swift": "Swift",
	".sh": "Shell",
	".bash": "Shell",
	".zsh": "Shell",
	".lua": "Lua",
	".ex": "Elixir",
	".exs": "Elixir",
	".dart": "Dart",
	".html": "HTML",
	".css": "CSS",
	".scss": "CSS",
	".vue": "Vue",
	".md": "Markdown",
	".toml": "TOML",
	".json": "JSON",
}


@dataclass
class Usage:
	files: int = 0
	directories: int = 0
	size: int = 0
	languages: dict[str, int] = field(default_factory=dict)

	@property
	def top_language(self) -> str:
		if not self.languages:
			return ""

		skip = {"Markdown", "JSON", "TOML"}

		ranked = sorted(self.languages.items(), key=lambda item: -item[1])

		for language, _ in ranked:
			if language not in skip:
				return language

		return ranked[0][0]


def disk_usage(path: str, ignore: Iterable[str] = ()) -> Usage:
	usage = Usage()
	skip = set(ignore)

	stack = [path]

	while stack:
		current = stack.pop()

		try:
			entries = list(os.scandir(current))
		except OSError:
			continue

		for entry in entries:
			try:
				if entry.is_dir(follow_symlinks=False):
					usage.directories += 1

					if entry.name not in skip:
						stack.append(entry.path)

					continue

				usage.files += 1
				usage.size += entry.stat(follow_symlinks=False).st_size

			except OSError:
				continue

			language = _LANGUAGE_BY_EXTENSION.get(Path(entry.name).suffix.lower())

			if language:
				usage.languages[language] = usage.languages.get(language, 0) + 1

	return usage
