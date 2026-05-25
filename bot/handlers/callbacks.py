import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes

from bot.models.database import AsyncSessionLocal, ReviewSchedule, VocabItem
from bot.services.user_service import (
    get_or_create_user, save_expression, mark_expression_known,
    set_user_mode, log_interaction, mark_review_sent,
)
from bot.services.content_generator import generate_more_examples, generate_challenge

logger = logging.getLogger(__name__)

MODE_NAMES = {
    "general": "🌐 General",
    "literary": "📖 Literary",
    "modern_native": "🗣 Modern Native",
    "business": "💼 Business",
    "cinematic": "🎬 Cinematic",
    "intellectual": "🧠 Intellectual",
    "music_culture": "🎵 Music & Culture",
}


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    tg_user = update.effective_user

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user.id, tg_user.username, tg_user.first_name)

        if data.startswith("save:"):
            expression = data[5:]
            await save_expression(session, user, expression, None, user.mode)
            await log_interaction(session, user.id, "save", expression)
            await query.answer(f"💾 Saved: {expression}", show_alert=False)

        elif data.startswith("known:"):
            expression = data[6:]
            await mark_expression_known(session, user, expression)
            await log_interaction(session, user.id, "known", expression)
            await query.answer(f"✅ Marked as known: {expression}", show_alert=True)

        elif data.startswith("examples:"):
            expression = data[9:]
            await log_interaction(session, user.id, "more_examples", expression)
            try:
                await query.message.reply_text("📖 Generating more examples…")
                examples = await generate_more_examples(expression)
                await query.message.reply_text(
                    f"📖 *More examples — {expression}*\n\n{examples}",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Error generating examples: {e}")
                await query.message.reply_text("⚠️ Couldn't generate examples. Try again shortly.")

        elif data.startswith("challenge:"):
            expression = data[10:]
            await log_interaction(session, user.id, "challenge", expression)
            try:
                await query.message.reply_text("⚡ Creating your challenge…")
                challenge = await generate_challenge(expression)
                await query.message.reply_text(
                    f"✏️ *Writing Challenge — {expression}*\n\n{challenge}",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Error generating challenge: {e}")
                await query.message.reply_text("⚠️ Couldn't generate challenge. Try again shortly.")

        elif data.startswith("later:"):
            expression = data[6:]
            await save_expression(session, user, expression, None, user.mode)
            await log_interaction(session, user.id, "later", expression)
            await query.answer("🔄 Saved — you'll be reminded in 3 days.", show_alert=True)

        elif data.startswith("mode:"):
            mode = data[5:]
            await set_user_mode(session, tg_user.id, mode)
            await log_interaction(session, user.id, "mode_change", mode)
            mode_name = MODE_NAMES.get(mode, mode)
            await query.edit_message_text(
                f"✅ *Mode set to {mode_name}*\n\nYour next daily pack will use this mode.\nUse /today to get a pack in your new mode right now.",
                parse_mode="Markdown",
            )

        elif data.startswith("review_known:"):
            parts = data.split(":", 2)
            review_id = int(parts[1])
            expression = parts[2]
            await mark_expression_known(session, user, expression)
            await mark_review_sent(session, review_id)
            await log_interaction(session, user.id, "review_known", expression)
            await query.edit_message_text(
                f"✅ *{expression}* marked as mastered.\n\nIt won't appear in future reviews.",
                parse_mode="Markdown",
            )

        elif data.startswith("review_again:"):
            parts = data.split(":", 2)
            review_id = int(parts[1])
            expression = parts[2]
            await mark_review_sent(session, review_id)

            result = await session.execute(
                select(VocabItem.id).where(
                    VocabItem.user_id == user.id,
                    VocabItem.expression == expression,
                )
            )
            vocab_id = result.scalar_one_or_none()

            if vocab_id:
                new_review = ReviewSchedule(
                    user_id=user.id,
                    vocab_item_id=vocab_id,
                    scheduled_at=datetime.utcnow() + timedelta(days=3),
                    interval_days=3,
                )
                session.add(new_review)
                await session.commit()

            await log_interaction(session, user.id, "review_again", expression)
            await query.edit_message_text(
                f"🔄 *{expression}* scheduled for another review in 3 days.",
                parse_mode="Markdown",
            )

        elif data == "cancel":
            await query.edit_message_reply_markup(reply_markup=None)
