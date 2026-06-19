"""Database operations for booking chat messages."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


async def list_messages(db: AsyncSession, booking_id: int) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.booking_id == booking_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def get_message(db: AsyncSession, message_id: int) -> Message | None:
    result = await db.execute(select(Message).where(Message.id == message_id))
    return result.scalar_one_or_none()


async def create_message(
    db: AsyncSession, booking_id: int, sender_id: int, body: str
) -> Message:
    msg = Message(booking_id=booking_id, sender_id=sender_id, body=body)
    db.add(msg)
    await db.commit()
    return await get_message(db, msg.id)
