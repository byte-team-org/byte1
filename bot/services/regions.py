from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from bot.models.region import RegionCapacity, REGIONS
from bot.config import settings


async def init_regions(session: AsyncSession):
    """Seed region capacity rows if they don't exist."""
    for region in REGIONS:
        result = await session.execute(
            select(RegionCapacity).where(RegionCapacity.region_name == region)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            limits_p = settings.region_limits_participants
            limits_v = settings.region_limits_volunteers
            session.add(RegionCapacity(
                region_name=region,
                max_participants=limits_p.get(region, 50),
                current_participants=0,
                max_volunteers=limits_v.get(region, 10),
                current_volunteers=0,
            ))
    await session.commit()


async def check_and_reserve_participant(session: AsyncSession, region: str) -> bool:
    """
    Atomically check if region has capacity for a participant and increment.
    Returns True if reservation was successful, False if full.
    """
    # Lock the row for update
    result = await session.execute(
        select(RegionCapacity)
        .where(RegionCapacity.region_name == region)
        .with_for_update()
    )
    capacity = result.scalar_one_or_none()
    if not capacity:
        return False
    if capacity.current_participants >= capacity.max_participants:
        return False
    capacity.current_participants += 1
    await session.commit()
    return True


async def check_and_reserve_volunteer(session: AsyncSession, region: str) -> bool:
    """
    Atomically check if region has capacity for a volunteer and increment.
    Returns True if reservation was successful, False if full.
    """
    result = await session.execute(
        select(RegionCapacity)
        .where(RegionCapacity.region_name == region)
        .with_for_update()
    )
    capacity = result.scalar_one_or_none()
    if not capacity:
        return False
    if capacity.current_volunteers >= capacity.max_volunteers:
        return False
    capacity.current_volunteers += 1
    await session.commit()
    return True


async def get_all_capacities(session: AsyncSession) -> list[RegionCapacity]:
    result = await session.execute(select(RegionCapacity))
    return result.scalars().all()
