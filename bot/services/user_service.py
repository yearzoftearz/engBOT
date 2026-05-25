from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.database import User, VocabItem, Interaction, ReviewSchedule, LearningMode


SPACED_REPETITION_INTERVALS = [3, 7, 21]


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None, first_name: str | None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_seen=datetime.utcnow(), username=username, first_name=first_name)
        )
        await session.commit()

    return user


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def set_user_mode(session: AsyncSession, telegram_id: int, mode: str) -> None:
    await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(mode=mode)
    )
    await session.commit()


async def set_daily_enabled(session: AsyncSession, telegram_id: int, enabled: bool) -> None:
    await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(daily_enabled=enabled)
    )
    await session.commit()


async def save_expression(
    session: AsyncSession,
    user: User,
    expression: str,
    definition_snippet: str | None,
    mode: str,
) -> VocabItem:
    result = await session.execute(
        select(VocabItem).where(
            VocabItem.user_id == user.id,
            VocabItem.expression == expression,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.times_seen += 1
        await session.commit()
        return existing

    item = VocabItem(
        user_id=user.id,
        expression=expression,
        definition_snippet=definition_snippet,
        mode=mode,
    )
    session.add(item)
    await session.flush()

    for days in SPACED_REPETITION_INTERVALS:
        review = ReviewSchedule(
            user_id=user.id,
            vocab_item_id=item.id,
            scheduled_at=datetime.utcnow() + timedelta(days=days),
            interval_days=days,
        )
        session.add(review)

    await session.commit()
    await session.refresh(item)
    return item


async def mark_expression_known(session: AsyncSession, user: User, expression: str) -> None:
    await session.execute(
        update(VocabItem)
        .where(VocabItem.user_id == user.id, VocabItem.expression == expression)
        .values(known=True)
    )
    await session.commit()


async def get_saved_vocab(session: AsyncSession, user_id: int) -> list[VocabItem]:
    result = await session.execute(
        select(VocabItem)
        .where(VocabItem.user_id == user_id)
        .order_by(VocabItem.saved_at.desc())
    )
    return list(result.scalars().all())


async def get_due_reviews(session: AsyncSession) -> list[ReviewSchedule]:
    result = await session.execute(
        select(ReviewSchedule)
        .where(ReviewSchedule.scheduled_at <= datetime.utcnow(), ReviewSchedule.sent == False)
    )
    return list(result.scalars().all())


async def mark_review_sent(session: AsyncSession, review_id: int) -> None:
    await session.execute(
        update(ReviewSchedule).where(ReviewSchedule.id == review_id).values(sent=True)
    )
    await session.commit()


async def log_interaction(session: AsyncSession, user_id: int, action: str, expression: str | None = None) -> None:
    interaction = Interaction(user_id=user_id, action=action, expression=expression)
    session.add(interaction)
    await session.commit()


async def get_all_active_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(User.is_active == True, User.daily_enabled == True)
    )
    return list(result.scalars().all())
