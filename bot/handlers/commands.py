import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.models.database import AsyncSessionLocal
from bot.services.user_service import (
    get_or_create_user, get_saved_vocab, set_daily_enabled, log_interaction
)
from bot.services.content_generator import generate_daily_pack
from bot.services.formatter import format_daily_pack, format_saved_list
from bot.keyboards import daily_pack_keyboard, mode_keyboard

logger = logging.getLogger(__name__)

START_TEXT = """👋 *Welcome to English Intelligence Bot*

I'm your daily companion for reaching native-level English fluency.

Every day I'll send you a curated *Daily English Intelligence Pack* — a deep dive into one expression: its nuance, collocations, cultural context, and how real native speakers use it.

This is not a quiz app. It's a *linguistic intelligence companion.*

━━━━━━━━━━━━━━━━━━━━━━

*Commands:*
/today — Get today's pack right now
/mode — Choose your learning mode
/save — View your saved expressions
/review — See expressions due for review
/pause — Pause daily messages
/resume — Resume daily messages
/help — Show this message

━━━━━━━━━━━━━━━━━━━━━━

Let's begin. Use /today to get your first pack."""

HELP_TEXT = """🧠 *English Intelligence Bot — Help*

*Daily Pack:* Sent every morning. One expression, fully unpacked.

*Commands:*
/today — Get today's pack immediately
/mode — Switch your learning mode
/save — Browse your saved expressions
/review — Review saved expressions (spaced repetition)
/pause — Stop daily messages temporarily
/resume — Restart daily messages

*Pack Buttons:*
💾 *Save* — Add to your personal vocabulary
✅ *I know this* — Mark as mastered
📖 *More examples* — Get 5 more usage examples
⚡ *Challenge me* — Get a creative writing challenge
🔄 *Repeat later* — Get reminded tomorrow

*Learning Modes:*
🌐 General — Balanced cultural & modern English
📖 Literary — Literature and poetic language
🗣 Modern Native — Contemporary speech and idioms
💼 Business — Professional communication
🎬 Cinematic — Film and TV dialogue
🧠 Intellectual — Academic and essay English
🎵 Music & Culture — Lyrical and pop culture language"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    async with AsyncSessionLocal() as session:
        await get_or_create_user(session, user.id, user.username, user.first_name)
        await log_interaction(session, user.id, "start")

    await update.message.reply_text(START_TEXT, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    msg = await update.message.reply_text("✨ Generating your daily pack…")

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.username, tg_user.first_name)
        mode = user.mode
        await log_interaction(session, user.id, "today")

    try:
        pack = await generate_daily_pack(mode)
        text = format_daily_pack(pack, mode)
        await msg.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=daily_pack_keyboard(pack["expression"]),
        )
    except Exception as e:
        logger.error(f"Error generating pack: {e}")
        await msg.edit_text("⚠️ Something went wrong generating your pack. Please try again in a moment.")


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🎛 *Choose Your Learning Mode*\n\n"
        "Each mode tunes the expressions, cultural references, and style to match your focus:\n\n"
        "🌐 *General* — Balanced mix of everything\n"
        "📖 *Literary* — Literature & poetic language\n"
        "🗣 *Modern Native* — Current speech & idioms\n"
        "💼 *Business* — Corporate & professional English\n"
        "🎬 *Cinematic* — Film & TV dialogue\n"
        "🧠 *Intellectual* — Academic & essay style\n"
        "🎵 *Music & Culture* — Lyrical & pop culture"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=mode_keyboard())


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.username, tg_user.first_name)
        items = await get_saved_vocab(session, user.id)

    text = format_saved_list(items)
    await update.message.reply_text(text, parse_mode="Markdown")


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.username, tg_user.first_name)
        from sqlalchemy import select
        from datetime import datetime
        from bot.models.database import ReviewSchedule
        result = await session.execute(
            select(ReviewSchedule)
            .where(
                ReviewSchedule.user_id == user.id,
                ReviewSchedule.scheduled_at <= datetime.utcnow(),
                ReviewSchedule.sent == False,
            )
        )
        reviews = result.scalars().all()

    if not reviews:
        await update.message.reply_text(
            "✅ *No reviews due right now.*\n\nKeep saving expressions and they'll appear here for spaced repetition review.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"🔄 *You have {len(reviews)} expression{'s' if len(reviews) != 1 else ''} to review.*\n\nReviews will be sent automatically at your daily pack time.",
        parse_mode="Markdown",
    )


async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.username, tg_user.first_name)
        await set_daily_enabled(session, tg_user.id, False)
        await log_interaction(session, user.id, "pause")

    await update.message.reply_text(
        "⏸ *Daily messages paused.*\n\nYou can still use /today any time. Use /resume to restart your daily pack.",
        parse_mode="Markdown",
    )


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.username, tg_user.first_name)
        await set_daily_enabled(session, tg_user.id, True)
        await log_interaction(session, user.id, "resume")

    await update.message.reply_text(
        "▶️ *Daily messages resumed.*\n\nYou'll receive your next pack tomorrow morning. Use /today for an immediate pack.",
        parse_mode="Markdown",
    )
