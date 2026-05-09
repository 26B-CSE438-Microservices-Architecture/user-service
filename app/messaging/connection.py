import asyncio
import logging

import aio_pika
from aio_pika import ExchangeType, RobustChannel, RobustConnection, RobustExchange

from app.config import settings

logger = logging.getLogger(__name__)

_connection: RobustConnection | None = None
_channel: RobustChannel | None = None

# Exchanges
user_events_exchange: RobustExchange | None = None
email_notifications_exchange: RobustExchange | None = None
user_commands_exchange: RobustExchange | None = None


async def connect() -> None:
    global _connection, _channel
    global user_events_exchange, email_notifications_exchange, user_commands_exchange

    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    _channel = await _connection.channel()
    await _channel.set_qos(prefetch_count=10)

    user_events_exchange = await _channel.declare_exchange(
        "user.events", ExchangeType.TOPIC, durable=True
    )
    email_notifications_exchange = await _channel.declare_exchange(
        "email.notifications", ExchangeType.DIRECT, durable=True
    )
    user_commands_exchange = await _channel.declare_exchange(
        "user.commands", ExchangeType.DIRECT, durable=True
    )

    # Declare queues and bind them
    email_queue = await _channel.declare_queue("email.send", durable=True)
    await email_queue.bind(email_notifications_exchange, routing_key="email.send")

    commands_queue = await _channel.declare_queue("user-service.commands", durable=True)
    await commands_queue.bind(user_commands_exchange, routing_key="user.commands")

    logger.info("RabbitMQ connection established")


async def disconnect() -> None:
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info("RabbitMQ connection closed")


def get_channel() -> RobustChannel:
    if _channel is None:
        raise RuntimeError("RabbitMQ channel is not initialized")
    return _channel
