import pytest

def test_create_item_by_volunteer(client, admin_token):
    response = client.post(
        "/api/knowledge/items",
        headers=admin_token,
        json={"title": "Test Title", "content": "Test Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Title"
    assert data["content"] == "Test Content"
    assert data["status"] == "draft"

def test_create_item_by_normal_user(client, normal_user_token):
    response = client.post(
        "/api/knowledge/items",
        headers=normal_user_token,
        json={"title": "Test Title", "content": "Test Content"}
    )
    assert response.status_code == 403

def test_create_item_unauthorized(client):
    response = client.post(
        "/api/knowledge/items",
        json={"title": "Test Title", "content": "Test Content"}
    )
    assert response.status_code == 401

def test_get_items_list(client, admin_token):
    # Create some items first
    client.post("/api/knowledge/items", headers=admin_token, json={"title": "Item 1", "content": "Content 1", "status": "published"})
    client.post("/api/knowledge/items", headers=admin_token, json={"title": "Item 2", "content": "Content 2", "status": "published"})
    
    response = client.get("/api/knowledge/items")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2

def test_get_item_detail(client, admin_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "Detail Item", "content": "Detail Content"})
    item_id = create_resp.json()["id"]
    
    response = client.get(f"/api/knowledge/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Detail Item"

def test_get_nonexistent_item_detail(client):
    response = client.get("/api/knowledge/items/9999")
    assert response.status_code == 404

def test_update_item_by_author(client, admin_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "Old Title", "content": "Old Content"})
    item_id = create_resp.json()["id"]
    
    response = client.put(
        f"/api/knowledge/items/{item_id}",
        headers=admin_token,
        json={"title": "New Title", "content": "New Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"

def test_update_item_by_non_author(client, admin_token, normal_user_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "Old Title", "content": "Old Content"})
    item_id = create_resp.json()["id"]
    
    response = client.put(
        f"/api/knowledge/items/{item_id}",
        headers=normal_user_token,
        json={"title": "New Title", "content": "New Content"}
    )
    assert response.status_code == 403

def test_update_item_by_expert(client, admin_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "Old Title", "content": "Old Content"})
    item_id = create_resp.json()["id"]
    
    response = client.put(
        f"/api/knowledge/items/{item_id}",
        headers=admin_token,
        json={"title": "Expert Title", "content": "Expert Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Expert Title"

def test_delete_item_by_author(client, admin_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "To Delete", "content": "Content"})
    item_id = create_resp.json()["id"]
    
    response = client.delete(f"/api/knowledge/items/{item_id}", headers=admin_token)
    assert response.status_code == 200
    
    get_resp = client.get(f"/api/knowledge/items/{item_id}")
    assert get_resp.status_code == 404

def test_delete_item_by_non_author(client, admin_token, normal_user_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "To Delete", "content": "Content"})
    item_id = create_resp.json()["id"]
    
    response = client.delete(f"/api/knowledge/items/{item_id}", headers=normal_user_token)
    assert response.status_code == 403

def test_get_audit_list_by_expert(client, admin_token):
    client.post("/api/knowledge/items", headers=admin_token, json={"title": "Pending Item", "content": "Content", "status": "pending_review"})
    
    response = client.get("/api/knowledge/audit-list", headers=admin_token)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["status"] == "pending_review"

def test_get_audit_list_unauthorized(client, normal_user_token):
    response = client.get("/api/knowledge/audit-list", headers=normal_user_token)
    assert response.status_code == 403

def test_audit_item_by_expert(client, admin_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "Pending Item", "content": "Content", "status": "pending_review"})
    item_id = create_resp.json()["id"]
    
    response = client.post(
        f"/api/knowledge/{item_id}/audit",
        headers=admin_token,
        json={"status": "published", "review_comments": "Looks good"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "published"
    assert data["review_comments"] == "Looks good"

def test_audit_item_unauthorized(client, admin_token, normal_user_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "Pending Item", "content": "Content", "status": "pending_review"})
    item_id = create_resp.json()["id"]
    
    response = client.post(
        f"/api/knowledge/{item_id}/audit",
        headers=normal_user_token,
        json={"status": "published", "review_comments": "Looks good"}
    )
    assert response.status_code == 403

def test_audit_item_invalid_status(client, admin_token):
    create_resp = client.post("/api/knowledge/items", headers=admin_token, json={"title": "Pending Item", "content": "Content", "status": "pending_review"})
    item_id = create_resp.json()["id"]
    
    response = client.post(
        f"/api/knowledge/{item_id}/audit",
        headers=admin_token,
        json={"status": "invalid_status", "review_comments": "Looks good"}
    )
    assert response.status_code == 422