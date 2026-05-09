import asyncio
import json
import logging
import smtplib
from email.message import EmailMessage

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.messaging.connection import get_channel

logger = logging.getLogger(__name__)


async def _handle_email(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            payload = json.loads(message.body)
            to_email = payload["to_email"]
            subject = payload["subject"]
            body = payload["body"]

            if not settings.SMTP_HOST:
                logger.warning("SMTP not configured, dropping email to %s", to_email)
                return

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email
            msg.set_content(body)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USERNAME:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                smtp.send_message(msg)

            logger.info("Email sent to %s", to_email)
        except Exception:
            logger.exception("Failed to process email message")


async def _handle_command(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            payload = json.loads(message.body)
            command_type = payload.get("command_type")

            if command_type in ("user.deactivate", "user.activate"):
                from app.models.user import User

                user_id = payload.get("user_id")
                if not user_id:
                    logger.warning("Received %s without user_id", command_type)
                    return

                is_active = command_type == "user.activate"
                async with async_session() as db:
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user is None:
                        logger.warning("Command %s: user %s not found", command_type, user_id)
                        return
                    user.is_active = is_active
                    await db.commit()
                    logger.info("User %s set is_active=%s via command", user_id, is_active)
            else:
                logger.warning("Unknown command_type: %s", command_type)
        except Exception:
            logger.exception("Failed to process command message")


async def start_consumers() -> None:
    channel = get_channel()

    email_queue = await channel.get_queue("email.send")
    await email_queue.consume(_handle_email)

    commands_queue = await channel.get_queue("user-service.commands")
    await commands_queue.consume(_handle_command)

    logger.info("RabbitMQ consumers started")
