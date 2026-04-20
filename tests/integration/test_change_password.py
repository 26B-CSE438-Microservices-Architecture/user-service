import uuid

from httpx import AsyncClient

from app.models.user import User

CHANGE_PASSWORD_URL = "/api/v1/users/me/change-password"


async def test_change_password_success(client: AsyncClient, test_user: User):
    response = await client.post(
        CHANGE_PASSWORD_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"current_password": "password123", "new_password": "newpassword456"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"


async def test_change_password_verifies_new_password_is_different(
    client: AsyncClient, test_user: User
):
    response = await client.post(
        CHANGE_PASSWORD_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"current_password": "password123", "new_password": "password123"},
    )

    assert response.status_code == 400
    assert "New password must be different" in response.json()["detail"]


async def test_change_password_wrong_current_returns_400(client: AsyncClient, test_user: User):
    response = await client.post(
        CHANGE_PASSWORD_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"current_password": "wrongpassword", "new_password": "newpassword456"},
    )

    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]


async def test_change_password_unknown_user_returns_404(client: AsyncClient):
    response = await client.post(
        CHANGE_PASSWORD_URL,
        headers={"X-User-Id": str(uuid.uuid4())},
        json={"current_password": "password123", "new_password": "newpassword456"},
    )

    assert response.status_code == 404


async def test_change_password_actually_updates_hash(client: AsyncClient, test_user: User, db_session):
    import bcrypt
    from sqlalchemy import select
    from app.models.user import User as UserModel

    await client.post(
        CHANGE_PASSWORD_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"current_password": "password123", "new_password": "brandnew789"},
    )

    await db_session.refresh(test_user)
    assert bcrypt.checkpw(b"brandnew789", test_user.hashed_password.encode())
    assert not bcrypt.checkpw(b"password123", test_user.hashed_password.encode())
