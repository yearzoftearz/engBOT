from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Text, ForeignKey, Enum
from datetime import datetime
import enum
import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///engbot.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class LearningMode(str, enum.Enum):
    GENERAL = "general"
    LITERARY = "literary"
    MODERN_NATIVE = "modern_native"
    BUSINESS = "business"
    CINEMATIC = "cinematic"
    INTELLECTUAL = "intellectual"
    MUSIC_CULTURE = "music_culture"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(32), default=LearningMode.GENERAL)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vocab_items: Mapped[list["VocabItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    interactions: Mapped[list["Interaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[list["ReviewSchedule"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class VocabItem(Base):
    __tablename__ = "vocab_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    expression: Mapped[str] = mapped_column(String(256), nullable=False)
    definition_snippet: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(32), default=LearningMode.GENERAL)
    saved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    times_seen: Mapped[int] = mapped_column(Integer, default=1)
    known: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="vocab_items")
    reviews: Mapped[list["ReviewSchedule"]] = relationship(back_populates="vocab_item", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    expression: Mapped[str | None] = mapped_column(String(256))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="interactions")


class ReviewSchedule(Base):
    __tablename__ = "review_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    vocab_item_id: Mapped[int] = mapped_column(ForeignKey("vocab_items.id"), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=3)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="reviews")
    vocab_item: Mapped["VocabItem"] = relationship(back_populates="reviews")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
