import logging
from django.conf import settings

logger = logging.getLogger(__name__)

EVENT_TYPE_EMOJI = {
    'watering': '💧',
    'fertilizing': '🌱',
    'pruning': '✂️',
    'other': '📋',
}


def format_notification_message(event, notification) -> str:
    from telegram.helpers import escape_markdown

    emoji = EVENT_TYPE_EMOJI.get(event.event_type, '📋')
    # General garden tasks have no plant: omit the plant line.
    plant_line = f"🌿 Plant: {escape_markdown(event.item.name)}\n" if event.item else ""
    # User-provided text is escaped so Telegram's legacy Markdown parser
    # never sees unbalanced entities (a bare '_' anywhere rejects the
    # whole message). The ack command's underscore is escaped the same way.
    return (
        f"🌸 *DaisyBlue Garden Reminder*\n\n"
        f"{emoji} *{escape_markdown(event.title)}*\n\n"
        f"📅 Date: {event.date.strftime('%B %d, %Y')}\n"
        f"{plant_line}"
        f"🏷️ Type: {event.get_event_type_display()}\n"
        f"🔄 Recurrence: {event.get_recurrence_display()}\n"
        f"\n{escape_markdown(event.description)}\n\n"
        f"✅ To acknowledge: /ack\\_{notification.id}"
    )


async def send_telegram_message(chat_id: str, text: str) -> str | None:
    """Send a Telegram message. Returns message_id or None on failure."""
    try:
        import telegram
        bot_token = settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not configured")
            return None
        bot = telegram.Bot(token=bot_token)
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='Markdown',
        )
        return str(message.message_id)
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return None


def send_notification_sync(chat_id: str, text: str) -> str | None:
    """Synchronous wrapper for Celery tasks."""
    import asyncio
    try:
        return asyncio.run(send_telegram_message(chat_id, text))
    except RuntimeError:
        # Event loop already running (shouldn't happen in Celery worker)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, send_telegram_message(chat_id, text))
            return future.result()
    except Exception as e:
        logger.error(f"Sync send failed: {e}")
        return None
