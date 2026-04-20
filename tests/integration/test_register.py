import pytest
from httpx import AsyncClient


REGISTER_URL = "/api/v1/users/register"

VALID_PAYLOAD = {
    "name": "Ahmet",
    "surname": "Yilmaz",
    "email": "ahmet@example.com",
    "phone": "5559876543",
    "password": "securepass1",
    "role": "CUSTOMER",
}


async def test_register_success(client: AsyncClient):
    response = await client.post(REGISTER_URL, json=VALID_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ahmet@example.com"
    assert data["name"] == "Ahmet"
    assert data["surname"] == "Yilmaz"
    assert data["phone"] == "5559876543"
    assert data["role"] == "CUSTOMER"
    assert "id" in data
    assert "created_at" in data


async def test_register_normalizes_email_to_lowercase(client: AsyncClient):
    payload = {**VALID_PAYLOAD, "email": "UPPER@EXAMPLE.COM", "phone": "5550000001"}
    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 201
    assert response.json()["email"] == "upper@example.com"


async def test_register_strips_whitespace_from_name(client: AsyncClient):
    payload = {**VALID_PAYLOAD, "name": "  Mehmet  ", "email": "mehmet@example.com", "phone": "5550000002"}
    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 201
    assert response.json()["name"] == "Mehmet"


async def test_register_duplicate_email_returns_409(client: AsyncClient, test_user):
    payload = {**VALID_PAYLOAD, "email": test_user.email, "phone": "5550000099"}
    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 409
    assert "Email or phone already exists" in response.json()["detail"]


async def test_register_duplicate_phone_returns_409(client: AsyncClient, test_user):
    payload = {**VALID_PAYLOAD, "email": "unique@example.com", "phone": test_user.phone}
    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 409
    assert "Email or phone already exists" in response.json()["detail"]


async def test_register_invalid_role_returns_400(client: AsyncClient):
    payload = {**VALID_PAYLOAD, "email": "role@example.com", "phone": "5550000003", "role": "SUPERADMIN"}
    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]


@pytest.mark.parametrize("role", ["CUSTOMER", "RESTAURANT_OWNER", "COURIER", "ADMIN"])
async def test_register_all_valid_roles(client: AsyncClient, role: str):
    payload = {
        "name": "Test",
        "surname": "Role",
        "email": f"{role.lower()}@example.com",
        "phone": f"555{abs(hash(role)) % 10000000:07d}"[:11],
        "password": "pass12345",
        "role": role,
    }
    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 201
    assert response.json()["role"] == role
