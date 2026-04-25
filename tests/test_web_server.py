import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_server_state():
    import web_server
    web_server._connections.clear()
    web_server._state["monitoring"] = False
    web_server._state["processing"] = False
    yield


def test_status_endpoint_returns_state():
    from web_server import app
    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["monitoring"] is False
    assert data["processing"] is False


def test_set_monitoring_updates_state():
    from web_server import app, set_monitoring
    set_monitoring(True)
    client = TestClient(app)
    response = client.get("/status")
    assert response.json()["monitoring"] is True


def test_set_processing_updates_state():
    from web_server import set_processing
    import web_server
    set_processing(True)
    assert web_server._state["processing"] is True


def test_websocket_receives_status_on_connect():
    from web_server import app
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        data = ws.receive_json()
        assert data["type"] == "status"
        assert "monitoring" in data
