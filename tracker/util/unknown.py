from typing import Any, Iterator


class Unknown:
	__slots__ = ()

	def __getitem__(self, key: object) -> "Unknown":
		return self

	def __getattr__(self, name: str) -> "Unknown":
		return self

	def get(self, key: object, default: Any = None) -> Any:
		return default if default is not None else self

	def __iter__(self) -> Iterator[Any]:
		return iter(())

	def __len__(self) -> int:
		return 0

	def __contains__(self, item: object) -> bool:
		return False

	def __eq__(self, other: object) -> bool:
		return isinstance(other, Unknown)

	def __hash__(self) -> int:
		return hash("<unknown>")

	def __str__(self) -> str:
		return "unknown"

	def __repr__(self) -> str:
		return "unknown"

	def __bool__(self) -> bool:
		return False
