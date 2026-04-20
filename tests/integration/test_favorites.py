from httpx import AsyncClient

from app.models.favorite import UserFavorite
from app.models.user import User

FAVORITES_URL = "/api/v1/users/me/favorites"


def _headers(user: User) -> dict:
    return {"X-User-Id": str(user.id)}


async def test_list_favorites_empty(client: AsyncClient, test_user: User):
    response = await client.get(FAVORITES_URL, headers=_headers(test_user))

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


async def test_add_favorite(client: AsyncClient, test_user: User):
    response = await client.post(
        f"{FAVORITES_URL}/vendor-abc", headers=_headers(test_user)
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Vendor added to favorites"


async def test_add_favorite_is_idempotent(client: AsyncClient, test_user: User):
    await client.post(f"{FAVORITES_URL}/vendor-abc", headers=_headers(test_user))
    response = await client.post(f"{FAVORITES_URL}/vendor-abc", headers=_headers(test_user))

    assert response.status_code == 200

    list_resp = await client.get(FAVORITES_URL, headers=_headers(test_user))
    assert list_resp.json()["total"] == 1


async def test_list_favorites_after_adding(client: AsyncClient, test_user: User):
    await client.post(f"{FAVORITES_URL}/vendor-1", headers=_headers(test_user))
    await client.post(f"{FAVORITES_URL}/vendor-2", headers=_headers(test_user))

    response = await client.get(FAVORITES_URL, headers=_headers(test_user))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    vendor_ids = {item["vendor_id"] for item in data["items"]}
    assert vendor_ids == {"vendor-1", "vendor-2"}


async def test_list_favorites_pagination(client: AsyncClient, test_user: User):
    for i in range(5):
        await client.post(f"{FAVORITES_URL}/vendor-{i}", headers=_headers(test_user))

    page1 = await client.get(f"{FAVORITES_URL}?page=1&size=3", headers=_headers(test_user))
    page2 = await client.get(f"{FAVORITES_URL}?page=2&size=3", headers=_headers(test_user))

    assert page1.status_code == 200
    assert page2.status_code == 200
    assert len(page1.json()["items"]) == 3
    assert len(page2.json()["items"]) == 2
    assert page1.json()["total"] == 5


async def test_remove_favorite(client: AsyncClient, test_user: User):
    await client.post(f"{FAVORITES_URL}/vendor-xyz", headers=_headers(test_user))

    response = await client.delete(f"{FAVORITES_URL}/vendor-xyz", headers=_headers(test_user))

    assert response.status_code == 200
    assert response.json()["message"] == "Vendor removed from favorites"

    list_resp = await client.get(FAVORITES_URL, headers=_headers(test_user))
    assert list_resp.json()["total"] == 0


async def test_remove_favorite_is_idempotent(client: AsyncClient, test_user: User):
    response = await client.delete(
        f"{FAVORITES_URL}/nonexistent-vendor", headers=_headers(test_user)
    )

    assert response.status_code == 200


async def test_list_favorites_ordered_by_created_at_desc(
    client: AsyncClient, test_user: User, db_session
):
    from datetime import datetime, timedelta, timezone

    fav1 = UserFavorite(
        user_id=test_user.id,
        vendor_id="old-vendor",
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    fav2 = UserFavorite(
        user_id=test_user.id,
        vendor_id="new-vendor",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(fav1)
    db_session.add(fav2)
    await db_session.commit()

    response = await client.get(FAVORITES_URL, headers=_headers(test_user))

    items = response.json()["items"]
    assert items[0]["vendor_id"] == "new-vendor"
    assert items[1]["vendor_id"] == "old-vendor"
