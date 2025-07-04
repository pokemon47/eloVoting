from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models import Poll, Option, VoterSession, MatchResult, GlobalScore
from app.schemas import PollCreate, OptionCreate, VoterSessionCreate, MatchResultCreate
from sqlalchemy.dialects.postgresql import insert

# Poll CRUDso 
async def create_poll(*, poll: PollCreate, session: AsyncSession) -> Poll:
    db_poll = Poll(**poll.model_dump())
    session.add(db_poll)
    await session.commit()
    await session.refresh(db_poll)
    return db_poll

async def get_poll_by_id(*, poll_id, session: AsyncSession) -> Optional[Poll]:
    result = await session.execute(select(Poll).where(Poll.id == poll_id))
    return result.scalar_one_or_none()

async def list_polls(session: AsyncSession) -> List[Poll]:
    result = await session.execute(select(Poll))
    return list(result.scalars().all())

# Option CRUD
async def create_option(*, option: OptionCreate, session: AsyncSession) -> Option:
    db_option = Option(**option.model_dump())
    session.add(db_option)
    await session.commit()
    await session.refresh(db_option)
    return db_option

async def get_option_by_id(*, option_id, session: AsyncSession) -> Optional[Option]:
    result = await session.execute(select(Option).where(Option.id == option_id))
    return result.scalar_one_or_none()

async def list_options_by_poll(*, poll_id, session: AsyncSession) -> List[Option]:
    result = await session.execute(select(Option).where(Option.poll_id == poll_id))
    return list(result.scalars().all())

# VoterSession CRUD
async def create_voter_session(*, session_data: VoterSessionCreate, session: AsyncSession) -> VoterSession:
    db_session = VoterSession(**session_data.model_dump())
    session.add(db_session)
    await session.commit()
    await session.refresh(db_session)
    return db_session

async def get_voter_session_by_id(*, session_id, session: AsyncSession) -> Optional[VoterSession]:
    result = await session.execute(select(VoterSession).where(VoterSession.id == session_id))
    return result.scalar_one_or_none()

# MatchResult CRUD
async def create_match_result(*, match: MatchResultCreate, session: AsyncSession) -> MatchResult:
    db_match = MatchResult(**match.model_dump())
    session.add(db_match)
    await session.commit()
    await session.refresh(db_match)
    return db_match

async def list_match_results_by_session(*, session_id, session: AsyncSession) -> List[MatchResult]:
    result = await session.execute(select(MatchResult).where(MatchResult.session_id == session_id))
    return list(result.scalars().all())

# GlobalScore CRUD
async def upsert_global_score(*, poll_id, option_id, total_score, session: AsyncSession):
    stmt = insert(GlobalScore).values(
        poll_id=poll_id,
        option_id=option_id,
        total_score=total_score
    ).on_conflict_do_update(
        index_elements=[GlobalScore.poll_id, GlobalScore.option_id],
        set_={
            'total_score': GlobalScore.total_score + total_score
        }
    )
    await session.execute(stmt)
    await session.commit()

async def list_global_scores_by_poll(*, poll_id, session: AsyncSession) -> List[GlobalScore]:
    result = await session.execute(select(GlobalScore).where(GlobalScore.poll_id == poll_id))
    return list(result.scalars().all()) 