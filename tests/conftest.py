import pytest

from dsound import config


@pytest.fixture
def out_dir(tmp_path, monkeypatch):
    """Carpeta de salida temporal (sin tocar ~/Music ni el .env)."""
    monkeypatch.setattr(config, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(config, "save_output_dir", lambda path: setattr(config, "OUTPUT_DIR", path))
    return tmp_path
