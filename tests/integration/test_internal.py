import uuid

from httpx import AsyncClient

from app.models.user import User

LOOKUP_URL = "/internal/v1/users/lookup"
BY_EMAIL_URL = "/internal/v1/users/by-email"


def _user_url(user_id) -> str:
    return f"/internal/v1/users/{user_id}"


async def test_lookup_returns_matched_users(client: AsyncClient, test_user: User):
    response = await client.post(LOOKUP_URL, json={"userIds": [str(test_user.id)]})

    assert response.status_code == 200
    users = response.json()["users"]
    assert len(users) == 1
    assert users[0]["id"] == str(test_user.id)
    assert users[0]["name"] == test_user.name
    assert users[0]["surname"] == test_user.surname
    assert users[0]["role"] == test_user.role.value
    assert users[0]["active"] is True


async def test_lookup_empty_list_returns_empty(client: AsyncClient):
    response = await client.post(LOOKUP_URL, json={"userIds": []})

    assert response.status_code == 200
    assert response.json()["users"] == []


async def test_lookup_unknown_ids_are_omitted(client: AsyncClient, test_user: User):
    response = await client.post(
        LOOKUP_URL,
        json={"userIds": [str(test_user.id), str(uuid.uuid4())]},
    )

    assert response.status_code == 200
    assert len(response.json()["users"]) == 1


async def test_lookup_multiple_users(client: AsyncClient, test_user: User, db_session):
    from app.models.user import UserRole
    from app.routers.users import hash_password

    second = User(
        name="Second",
        surname="User",
        email="second@example.com",
        phone="5550000044",
        hashed_password=hash_password("pass"),
        role=UserRole.COURIER,
    )
    db_session.add(second)
    await db_session.commit()
    await db_session.refresh(second)

    response = await client.post(
        LOOKUP_URL,
        json={"userIds": [str(test_user.id), str(second.id)]},
    )

    assert response.status_code == 200
    assert len(response.json()["users"]) == 2


async def test_get_by_email_found(client: AsyncClient, test_user: User):
    response = await client.get(BY_EMAIL_URL, params={"email": test_user.email})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert "hashedPassword" in data
    assert data["role"] == test_user.role.value
    assert data["active"] is True


async def test_get_by_email_case_insensitive(client: AsyncClient, test_user: User):
    response = await client.get(BY_EMAIL_URL, params={"email": test_user.email.upper()})

    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


async def test_get_by_email_not_found_returns_404(client: AsyncClient):
    response = await client.get(BY_EMAIL_URL, params={"email": "nobody@example.com"})

    assert response.status_code == 404


async def test_get_by_id_found(client: AsyncClient, test_user: User):
    response = await client.get(_user_url(test_user.id))

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["name"] == test_user.name
    assert data["email"] == test_user.email
    assert data["phone"] == test_user.phone
    assert data["role"] == test_user.role.value
    assert data["active"] is True


async def test_get_by_id_not_found_returns_404(client: AsyncClient):
    response = await client.get(_user_url(uuid.uuid4()))

    assert response.status_code == 404
