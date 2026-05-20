from pathlib import Path


_backend_apps_path = Path(__file__).resolve().parent.parent / "backend" / "apps"
__path__ = [str(_backend_apps_path)]
