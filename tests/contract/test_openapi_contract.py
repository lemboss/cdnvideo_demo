import json
from pathlib import Path

from app.core.config import Environment, Settings
from app.main import create_app
from tests.conftest import TEST_API_KEY, TEST_YANDEX_GEOCODER_API_KEY


def test_openapi_schema_matches_snapshot() -> None:
    settings = Settings(
        environment=Environment.TESTING,
        api_key=TEST_API_KEY,
        rate_limit_enabled=False,
        yandex_geocoder_api_key=TEST_YANDEX_GEOCODER_API_KEY,
    )
    app = create_app(settings=settings)
    schema = app.openapi()

    snapshot_path = Path(__file__).with_name("openapi_snapshot.json")
    expected = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert schema == expected
