import dataclasses
import json
import logging

from aio_pika import DeliveryMode, Message

from app.messaging import connection
from app.messaging.events import SendEmailCommand

logger = logging.getLogger(__name__)


def _to_message(payload: object) -> Message:
    body = json.dumps(dataclasses.asdict(payload)).encode()
    return Message(body, delivery_mode=DeliveryMode.PERSISTENT, content_type="application/json")


async def publish_user_event(event: object, routing_key: str) -> None:
    try:
        exchange = connection.user_events_exchange
        if exchange is None:
            logger.warning("user.events exchange not ready, skipping publish")
            return
        await exchange.publish(_to_message(event), routing_key=routing_key)
    except Exception:
        logger.exception("Failed to publish user event with routing_key=%s", routing_key)


async def publish_send_email(command: SendEmailCommand) -> None:
    try:
        exchange = connection.email_notifications_exchange
        if exchange is None:
            logger.warning("email.notifications exchange not ready, skipping publish")
            return
        await exchange.publish(_to_message(command), routing_key="email.send")
    except Exception:
        logger.exception("Failed to publish send_email command")
