from pathlib import Path


_backend_config_path = Path(__file__).resolve().parent.parent / "backend" / "config"
__path__ = [str(_backend_config_path)]
