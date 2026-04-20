import uuid

from httpx import AsyncClient

from app.models.user import User

ME_URL = "/api/v1/users/me"


async def test_get_me_returns_user_profile(client: AsyncClient, test_user: User):
    response = await client.get(ME_URL, headers={"X-User-Id": str(test_user.id)})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == f"user_{test_user.id}"
    assert data["name"] == test_user.name
    assert data["surname"] == test_user.surname
    assert data["email"] == test_user.email
    assert data["phone_number"] == test_user.phone
    assert data["role"] == test_user.role.value
    assert data["is_active"] is True
    assert data["addresses"] == []


async def test_get_me_includes_addresses(client: AsyncClient, test_user: User, test_address):
    response = await client.get(ME_URL, headers={"X-User-Id": str(test_user.id)})

    assert response.status_code == 200
    addresses = response.json()["addresses"]
    assert len(addresses) == 1
    assert addresses[0]["address_title"] == test_address.address_title


async def test_get_me_unknown_user_returns_404(client: AsyncClient):
    response = await client.get(ME_URL, headers={"X-User-Id": str(uuid.uuid4())})

    assert response.status_code == 404


async def test_get_me_invalid_uuid_header_returns_400(client: AsyncClient):
    response = await client.get(ME_URL, headers={"X-User-Id": "not-a-uuid"})

    assert response.status_code == 400
    assert "Invalid X-User-Id header" in response.json()["detail"]


async def test_update_me_name(client: AsyncClient, test_user: User):
    response = await client.put(
        ME_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"name": "Yeni"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Yeni"


async def test_update_me_phone(client: AsyncClient, test_user: User):
    response = await client.put(
        ME_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"phone": "5550000011"},
    )

    assert response.status_code == 200
    assert response.json()["phone_number"] == "5550000011"


async def test_update_me_phone_conflict_returns_409(
    client: AsyncClient, test_user: User, db_session
):
    from app.models.user import UserRole
    from app.routers.users import hash_password

    other = User(
        name="Other",
        surname="User",
        email="other@example.com",
        phone="5550000022",
        hashed_password=hash_password("pass"),
        role=UserRole.CUSTOMER,
    )
    db_session.add(other)
    await db_session.commit()

    response = await client.put(
        ME_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"phone": "5550000022"},
    )

    assert response.status_code == 409
    assert "Phone already exists" in response.json()["detail"]


async def test_update_me_no_fields_returns_400(client: AsyncClient, test_user: User):
    response = await client.put(ME_URL, headers={"X-User-Id": str(test_user.id)}, json={})

    assert response.status_code == 400
    assert "At least one field" in response.json()["detail"]


async def test_update_me_strips_whitespace(client: AsyncClient, test_user: User):
    response = await client.put(
        ME_URL,
        headers={"X-User-Id": str(test_user.id)},
        json={"name": "  Trimmed  "},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Trimmed"
