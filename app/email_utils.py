import smtplib
from email.message import EmailMessage

from app.config import settings


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = "Reset your password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        (
            "You requested a password reset.\n\n"
            f"Reset link: {reset_link}\n\n"
            f"This link expires in {settings.RESET_PASSWORD_TOKEN_TTL_MINUTES} minutes."
        )
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
