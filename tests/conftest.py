import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app import create_app
from backend.extensions import db

@pytest.fixture()
def app(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}", "UPLOAD_FOLDER": tmp_path / "uploads", "RATELIMIT_ENABLED": False, "SECRET_KEY": "test"})
    with app.app_context():
        db.drop_all(); db.create_all()
    yield app

@pytest.fixture()
def client(app): return app.test_client()
