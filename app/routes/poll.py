from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas import PollCreate, PollOut
from app.crud import create_poll, list_polls, get_poll_by_id
from app.database import get_async_session
from app.routes.auth import get_current_user

router = APIRouter(prefix="/polls", tags=["polls"])

@router.post("/", response_model=PollOut)
async def create_poll_endpoint(
    poll: PollCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user)
) -> PollOut:
    return await create_poll(poll=poll, session=session)

@router.get("/", response_model=List[PollOut])
async def list_polls_endpoint(
    session: AsyncSession = Depends(get_async_session)
) -> List[PollOut]:
    return await list_polls(session=session)

@router.get("/{poll_id}", response_model=PollOut)
async def get_poll_by_id_endpoint(
    poll_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> PollOut:
    poll = await get_poll_by_id(poll_id=poll_id, session=session)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll 