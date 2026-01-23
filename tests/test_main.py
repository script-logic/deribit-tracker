from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "root"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_metadata():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert "info" in data
    assert "Deribit Tracker" in data["info"]["title"]
    assert "0.2.0" in data["info"]["version"]


def test_cors_headers():
    """Test CORS headers are properly configured."""
    response = client.get(
        "/",
        headers={"Origin": "http://127.0.0.1:8000"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

    response_options = client.options(
        "/",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response_options.status_code == 200
    assert "access-control-allow-origin" in response_options.headers
    assert (
        response_options.headers["access-control-allow-origin"]
        == "http://127.0.0.1:8000"
    )


def test_nonexistent_endpoint():
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "detail" in response.json()
