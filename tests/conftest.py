import pytest

class DummyClient:
    """Placeholder HTTP client for tests."""

    def post(self, path: str, json: dict):
        raise NotImplementedError("publish not implemented")

    def wait_for(self, topic: str, timeout: int = 30):
        raise NotImplementedError("wait_for not implemented")

@pytest.fixture
def client():
    return DummyClient()
