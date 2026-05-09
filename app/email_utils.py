from app.config import settings
from app.messaging.events import SendEmailCommand
from app.messaging.publisher import publish_send_email


async def enqueue_password_reset_email(to_email: str, reset_link: str) -> None:
    body = (
        "You requested a password reset.\n\n"
        f"Reset link: {reset_link}\n\n"
        f"This link expires in {settings.RESET_PASSWORD_TOKEN_TTL_MINUTES} minutes."
    )
    command = SendEmailCommand(
        to_email=to_email,
        subject="Reset your password",
        body=body,
    )
    await publish_send_email(command)
