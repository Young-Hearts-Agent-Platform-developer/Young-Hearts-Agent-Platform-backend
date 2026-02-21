def test_health(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
