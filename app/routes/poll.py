from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.schemas import PollCreate, PollOut, LeaderboardEntry, LeaderboardResponse
from app.crud import create_poll, list_polls, get_poll_by_id, list_options_by_poll, list_global_scores_by_poll, get_voter_session_by_id
from app.database import get_async_session
from app.routes.auth import get_current_user
from uuid import UUID
import random

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
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user)  # Add auth requirement
):
    """List all polls. Requires authentication to prevent unauthorized access."""
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

@router.get("/{poll_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    poll_id: str,
    view_all: bool = Query(False, description="Return all options if true, else top 10"),
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user)
):
    # 1. Check poll exists
    poll = await get_poll_by_id(poll_id=poll_id, session=session)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found or no longer exists")

    # 2. Get user info
    user_id = user.get("sub")
    user_email = user.get("email")
    user_role = user.get("role") or user.get("is_superadmin")

    # 3. Check if user is poll creator, superadmin, or has completed session
    is_creator = (poll.creator_email == user_email)
    is_superadmin = (user_role == "superadmin" or user_role is True)
    has_voted = False
    # Check for completed session for this poll and user
    from app.models import VoterSession
    from sqlalchemy import select
    result = await session.execute(
        select(VoterSession).where(
            (VoterSession.poll_id == poll_id) &
            (VoterSession.voter_email == user_email) &
            (VoterSession.is_complete == True)
        )
    )
    if result.scalar_one_or_none():
        has_voted = True
    if not (is_creator or is_superadmin or has_voted):
        raise HTTPException(status_code=403, detail="Not authorized to view leaderboard for this poll")

    # 4. Get all options for the poll
    options = await list_options_by_poll(poll_id=poll_id, session=session)
    option_id_to_label = {str(option.id): option.label for option in options}

    # 5. Get global scores for the poll
    global_scores = await list_global_scores_by_poll(poll_id=poll_id, session=session)
    option_id_to_score = {str(score.option_id): score.total_score for score in global_scores}

    # 6. Build leaderboard entries
    entries = []
    if global_scores:
        # There are votes, so build leaderboard with scores
        for option in options:
            score = option_id_to_score.get(str(option.id), 0.0)
            entries.append({
                "label": option.label,
                "score": score,
                "option_id": str(option.id)
            })
        # Sort by score descending, stable by previous order
        entries.sort(key=lambda x: (-x["score"]))
        # Assign ranks (ties share rank, stable order)
        leaderboard = []
        prev_score = None
        prev_rank = 0
        for idx, entry in enumerate(entries):
            if prev_score is not None and entry["score"] == prev_score:
                rank = prev_rank
            else:
                rank = idx + 1
            leaderboard.append(LeaderboardEntry(label=entry["label"], score=entry["score"], rank=rank))
            prev_score = entry["score"]
            prev_rank = rank
    else:
        # No votes yet: show all options, random order, score 0, rank 'NA'
        random.shuffle(options)
        leaderboard = [LeaderboardEntry(label=option.label, score=0.0, rank="NA") for option in options]
        if not view_all:
            leaderboard = leaderboard[:10]
        return LeaderboardResponse(leaderboard=leaderboard)

    # 7. Pagination: top 10 or all
    if not view_all:
        leaderboard = leaderboard[:10]

    return LeaderboardResponse(leaderboard=leaderboard) 