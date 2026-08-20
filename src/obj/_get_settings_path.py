from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

settings_path = PROJECT_ROOT / "settings.toml"
my_settings_path = PROJECT_ROOT / "my_settings.toml"

if my_settings_path.exists():
	settings_path = my_settings_path
