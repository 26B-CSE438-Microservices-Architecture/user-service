from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient

from app.models.user import User

REQUEST_URL = "/api/v1/users/forgot-password/request"
CONFIRM_URL = "/api/v1/users/forgot-password/confirm"

_EMAIL_PATCH = "app.routers.users.send_password_reset_email"


def _extract_token(reset_link: str) -> str:
    return parse_qs(urlparse(reset_link).query)["token"][0]


async def test_request_sends_email_and_creates_token(client: AsyncClient, test_user: User):
    with patch(_EMAIL_PATCH) as mock_send:
        response = await client.post(REQUEST_URL, json={"email": test_user.email})

    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"]
    mock_send.assert_called_once()
    to_email, reset_link = mock_send.call_args[0]
    assert to_email == test_user.email
    assert "token=" in reset_link


async def test_request_unknown_email_returns_same_message(client: AsyncClient):
    with patch(_EMAIL_PATCH) as mock_send:
        response = await client.post(REQUEST_URL, json={"email": "nobody@example.com"})

    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"]
    mock_send.assert_not_called()


async def test_request_smtp_failure_returns_503(client: AsyncClient, test_user: User):
    with patch(_EMAIL_PATCH, side_effect=Exception("SMTP error")):
        response = await client.post(REQUEST_URL, json={"email": test_user.email})

    assert response.status_code == 503
    assert "Failed to send reset email" in response.json()["detail"]


async def test_confirm_resets_password(client: AsyncClient, test_user: User):
    with patch(_EMAIL_PATCH) as mock_send:
        await client.post(REQUEST_URL, json={"email": test_user.email})
        reset_link = mock_send.call_args[0][1]

    raw_token = _extract_token(reset_link)
    response = await client.post(
        CONFIRM_URL, json={"token": raw_token, "new_password": "resetted999"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"


async def test_confirm_verifies_new_password_differs(client: AsyncClient, test_user: User):
    with patch(_EMAIL_PATCH) as mock_send:
        await client.post(REQUEST_URL, json={"email": test_user.email})
        reset_link = mock_send.call_args[0][1]

    raw_token = _extract_token(reset_link)
    response = await client.post(
        CONFIRM_URL, json={"token": raw_token, "new_password": "password123"}
    )

    assert response.status_code == 400
    assert "New password must be different" in response.json()["detail"]


async def test_confirm_invalid_token_returns_400(client: AsyncClient):
    response = await client.post(
        CONFIRM_URL, json={"token": "totallyinvalidtoken", "new_password": "newpass999"}
    )

    assert response.status_code == 400
    assert "Invalid or expired token" in response.json()["detail"]


async def test_confirm_token_cannot_be_reused(client: AsyncClient, test_user: User):
    with patch(_EMAIL_PATCH) as mock_send:
        await client.post(REQUEST_URL, json={"email": test_user.email})
        reset_link = mock_send.call_args[0][1]

    raw_token = _extract_token(reset_link)
    payload = {"token": raw_token, "new_password": "firstchange111"}

    first = await client.post(CONFIRM_URL, json=payload)
    assert first.status_code == 200

    second = await client.post(CONFIRM_URL, json=payload)
    assert second.status_code == 400


async def test_confirm_normalizes_email_case_in_request(client: AsyncClient, test_user: User):
    with patch(_EMAIL_PATCH) as mock_send:
        await client.post(REQUEST_URL, json={"email": test_user.email.upper()})

    mock_send.assert_called_once()
