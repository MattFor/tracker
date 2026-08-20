import os


def walk(path: str, proj: str) -> dict | False:
	for root, dirs, files in os.walk(path):
		print(root)

		# noinspection shadowing-builtins
		for dir in dirs:
			if dir.lower() == proj.lower():
				return {
					"path": dir,
				}

	return False
