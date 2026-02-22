import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.services.auth_service import get_current_user
import os

client = TestClient(app)

def override_get_current_user():
    user = User(id=1, username="test_expert", roles='["expert"]')
    return user

app.dependency_overrides[get_current_user] = override_get_current_user

def test_upload_text():
    response = client.post(
        "/api/knowledge/upload",
        data={
            "title": "test_text_upload",
            "text_content": "This is a test text content.",
            "category": "test",
            "risk_level": "low"
        }
    )
    assert response.status_code == 200
    assert "item_id" in response.json()
    
    # Check if file is created
    files = os.listdir("./data/raw_data")
    found = False
    for f in files:
        if "test_text_upload.txt" in f:
            found = True
            break
    assert found

def test_upload_file():
    file_content = b"This is a test file content."
    response = client.post(
        "/api/knowledge/upload",
        data={
            "category": "test",
            "risk_level": "low"
        },
        files={"file": ("test_file_upload.txt", file_content, "text/plain")}
    )
    assert response.status_code == 200
    assert "item_id" in response.json()
    
    # Check if file is created
    files = os.listdir("./data/raw_data")
    found = False
    for f in files:
        if "test_file_upload.txt" in f:
            found = True
            break
    assert found
