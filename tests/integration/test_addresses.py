import uuid

from httpx import AsyncClient

from app.models.user import User

ADDRESSES_URL = "/api/v1/users/me/addresses"

VALID_ADDRESS = {
    "address_title": "Office",
    "city": "Ankara",
    "district": "Cankaya",
    "neighborhood": "Kizilay",
    "street": "Ataturk Bulvari",
    "building_no": "10",
    "floor": "3",
    "apartment_no": "12",
    "phone": "5559990000",
}


async def test_list_addresses_empty(client: AsyncClient, test_user: User):
    response = await client.get(ADDRESSES_URL, headers={"X-User-Id": str(test_user.id)})

    assert response.status_code == 200
    assert response.json() == []


async def test_list_addresses_returns_existing(client: AsyncClient, test_user: User, test_address):
    response = await client.get(ADDRESSES_URL, headers={"X-User-Id": str(test_user.id)})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["address_title"] == test_address.address_title
    assert data[0]["city"] == test_address.city
    assert data[0]["id"].startswith("addr_")


async def test_list_addresses_excludes_soft_deleted(
    client: AsyncClient, test_user: User, test_address, db_session
):
    from datetime import datetime, timezone

    test_address.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    response = await client.get(ADDRESSES_URL, headers={"X-User-Id": str(test_user.id)})

    assert response.status_code == 200
    assert response.json() == []


async def test_create_address(client: AsyncClient, test_user: User):
    response = await client.post(
        ADDRESSES_URL,
        headers={"X-User-Id": str(test_user.id)},
        json=VALID_ADDRESS,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["address_title"] == "Office"
    assert data["city"] == "Ankara"
    assert data["id"].startswith("addr_")
    assert data["location"] == {"lat": None, "lng": None}


async def test_create_address_with_location(client: AsyncClient, test_user: User):
    payload = {**VALID_ADDRESS, "location": {"lat": 39.9334, "lng": 32.8597}}
    response = await client.post(
        ADDRESSES_URL,
        headers={"X-User-Id": str(test_user.id)},
        json=payload,
    )

    assert response.status_code == 201
    location = response.json()["location"]
    assert location["lat"] == 39.9334
    assert location["lng"] == 32.8597


async def test_update_address_city(client: AsyncClient, test_user: User, test_address):
    addr_id = f"addr_{test_address.id}"
    response = await client.put(
        f"{ADDRESSES_URL}/{addr_id}",
        headers={"X-User-Id": str(test_user.id)},
        json={"city": "Izmir"},
    )

    assert response.status_code == 200
    assert response.json()["city"] == "Izmir"


async def test_update_address_not_found_returns_404(client: AsyncClient, test_user: User):
    fake_id = f"addr_{uuid.uuid4()}"
    response = await client.put(
        f"{ADDRESSES_URL}/{fake_id}",
        headers={"X-User-Id": str(test_user.id)},
        json={"city": "Izmir"},
    )

    assert response.status_code == 404


async def test_update_address_invalid_id_returns_400(client: AsyncClient, test_user: User):
    response = await client.put(
        f"{ADDRESSES_URL}/not-valid",
        headers={"X-User-Id": str(test_user.id)},
        json={"city": "Izmir"},
    )

    assert response.status_code == 400


async def test_delete_address_soft_deletes(client: AsyncClient, test_user: User, test_address):
    addr_id = f"addr_{test_address.id}"
    response = await client.delete(
        f"{ADDRESSES_URL}/{addr_id}",
        headers={"X-User-Id": str(test_user.id)},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Address deleted"

    list_response = await client.get(ADDRESSES_URL, headers={"X-User-Id": str(test_user.id)})
    assert list_response.json() == []


async def test_delete_address_not_found_returns_404(client: AsyncClient, test_user: User):
    fake_id = f"addr_{uuid.uuid4()}"
    response = await client.delete(
        f"{ADDRESSES_URL}/{fake_id}",
        headers={"X-User-Id": str(test_user.id)},
    )

    assert response.status_code == 404


async def test_set_current_address(client: AsyncClient, test_user: User, db_session):
    from app.models.address import Address

    addr1 = Address(
        user_id=test_user.id,
        address_title="Home",
        city="Istanbul",
        district="D",
        neighborhood="N",
        street="S",
        building_no="1",
        floor="1",
        apartment_no="1",
        phone="5550000001",
        is_current=True,
    )
    addr2 = Address(
        user_id=test_user.id,
        address_title="Work",
        city="Ankara",
        district="D",
        neighborhood="N",
        street="S",
        building_no="2",
        floor="2",
        apartment_no="2",
        phone="5550000002",
        is_current=False,
    )
    db_session.add(addr1)
    db_session.add(addr2)
    await db_session.commit()
    await db_session.refresh(addr2)

    response = await client.patch(
        f"{ADDRESSES_URL}/addr_{addr2.id}/current",
        headers={"X-User-Id": str(test_user.id)},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Current address updated"

    list_resp = await client.get(ADDRESSES_URL, headers={"X-User-Id": str(test_user.id)})
    addresses = list_resp.json()
    current = [a for a in addresses if a["is_current"]]
    assert len(current) == 1
    assert current[0]["address_title"] == "Work"


async def test_set_current_address_not_found_returns_404(client: AsyncClient, test_user: User):
    fake_id = f"addr_{uuid.uuid4()}"
    response = await client.patch(
        f"{ADDRESSES_URL}/{fake_id}/current",
        headers={"X-User-Id": str(test_user.id)},
    )

    assert response.status_code == 404
