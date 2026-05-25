import logging
import os
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from telegram.error import TelegramError

from bot.models.database import AsyncSessionLocal, LearningMode
from bot.services.content_generator import generate_daily_pack
from bot.services.user_service import get_all_active_users, get_due_reviews, mark_review_sent
from bot.services.formatter import format_daily_pack, format_review_pack
from bot.keyboards import daily_pack_keyboard, review_keyboard

logger = logging.getLogger(__name__)


async def send_daily_pack(bot: Bot) -> None:
    logger.info("Sending daily packs...")
    async with AsyncSessionLocal() as session:
        users = await get_all_active_users(session)

    packs_cache: dict[str, dict] = {}

    for user in users:
        mode = user.mode or LearningMode.GENERAL
        if mode not in packs_cache:
            try:
                packs_cache[mode] = await generate_daily_pack(mode)
            except Exception as e:
                logger.error(f"Failed to generate pack for mode {mode}: {e}")
                continue

        pack = packs_cache[mode]
        text = format_daily_pack(pack, mode)

        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=daily_pack_keyboard(pack["expression"]),
            )
            logger.info(f"Sent daily pack to user {user.telegram_id}")
        except TelegramError as e:
            logger.warning(f"Failed to send to {user.telegram_id}: {e}")


async def send_due_reviews(bot: Bot) -> None:
    async with AsyncSessionLocal() as session:
        reviews = await get_due_reviews(session)

        for review in reviews:
            vocab = review.vocab_item
            user = review.user
            text = format_review_pack(
                expression=vocab.expression,
                definition_snippet=vocab.definition_snippet,
                times_seen=vocab.times_seen,
            )
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=review_keyboard(vocab.expression, review.id),
                )
                await mark_review_sent(session, review.id)
            except TelegramError as e:
                logger.warning(f"Failed to send review to {user.telegram_id}: {e}")


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    tz = pytz.timezone(os.getenv("TIMEZONE", "UTC"))
    daily_hour = int(os.getenv("DAILY_HOUR", "9"))
    daily_minute = int(os.getenv("DAILY_MINUTE", "0"))

    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        send_daily_pack,
        trigger=CronTrigger(hour=daily_hour, minute=daily_minute, timezone=tz),
        args=[bot],
        id="daily_pack",
        name="Daily English Pack",
        replace_existing=True,
    )

    scheduler.add_job(
        send_due_reviews,
        trigger=CronTrigger(hour=daily_hour, minute=daily_minute + 5, timezone=tz),
        args=[bot],
        id="spaced_reviews",
        name="Spaced Repetition Reviews",
        replace_existing=True,
    )

    return scheduler
