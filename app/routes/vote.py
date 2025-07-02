from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.schemas import VoterSessionCreate, VoterSessionOut, MatchResultCreate, MatchResultOut, LeaderboardEntry, LeaderboardResponse
from app.crud import create_voter_session, get_voter_session_by_id, create_match_result, list_match_results_by_session, list_options_by_poll, upsert_global_score
from app.database import get_async_session
from app.routes.auth import get_current_user
from app.elo import process_session_elo, mean_center
from typing import Dict, Any

router = APIRouter(prefix="/votes", tags=["votes"])

@router.post("/session/", response_model=VoterSessionOut)
async def start_voter_session(
    session_data: VoterSessionCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user)
):
    return await create_voter_session(session_data=session_data, session=session)

@router.post("/match/", response_model=MatchResultOut)
async def submit_match_result(
    match: MatchResultCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user)
):
    return await create_match_result(match=match, session=session)

@router.get("/session/{session_id}/results", response_model=list[MatchResultOut])
async def get_session_results(
    session_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    return await list_match_results_by_session(session_id=session_id, session=session)

@router.post("/session/{session_id}/complete")
async def complete_voter_session(
    session_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user)
):
    """
    Complete a voter session and aggregate results into global scores.
    
    Validates session ownership, checks completion, calculates Elo scores,
    normalizes them, and adds to global leaderboard.
    """
    # Get the voter session
    voter_session = await get_voter_session_by_id(session_id=session_id, session=session)
    if not voter_session:
        raise HTTPException(status_code=404, detail="Voter session not found")
    
    # Validate session ownership
    if voter_session.voter_email != user.get("email"):
        raise HTTPException(status_code=403, detail="Not authorized to complete this session")
    
    # Check if session is already complete
    if voter_session.is_complete:
        raise HTTPException(status_code=400, detail="Session is already complete")
    
    # Get all options for the poll
    options = await list_options_by_poll(poll_id=voter_session.poll_id, session=session)
    n_options = len(options)
    expected_matches = n_options * (n_options - 1) // 2
    
    # Get all match results for this session
    match_results = await list_match_results_by_session(session_id=session_id, session=session)
    
    # Validate that all matches are completed
    if len(match_results) != expected_matches:
        raise HTTPException(
            status_code=400, 
            detail=f"Session incomplete. Expected {expected_matches} matches, got {len(match_results)}"
        )
    
    # Calculate Elo scores for the session
    elo_scores = process_session_elo(match_results=match_results, options=options)
    
    # Normalize the scores (mean-center)
    normalized_scores = mean_center(elo_scores)
    
    # Aggregate normalized scores into global scores
    for option, normalized_score in zip(options, normalized_scores):
        await upsert_global_score(
            poll_id=voter_session.poll_id,
            option_id=option.id,
            delta=normalized_score,
            batch_size=1,
            session=session
        )
    
    # Mark session as complete
    voter_session.is_complete = True
    await session.commit()
    await session.refresh(voter_session)
    
    return {"message": "Session completed successfully", "session_id": str(session_id)}

@router.get("/session/{session_id}/leaderboard", response_model=LeaderboardResponse)
async def get_session_leaderboard(
    session_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user)
):
    """
    Return the Elo vector for a completed session as a leaderboard.
    Only the session owner or superadmin can access.
    """
    from app.models import VoterSession
    from sqlalchemy import select
    # 1. Get the session
    voter_session = await get_voter_session_by_id(session_id=session_id, session=session)
    if not voter_session:
        raise HTTPException(status_code=404, detail="Session not found")
    # 2. Access control
    user_email = user.get("email")
    user_role = user.get("role") or user.get("is_superadmin")
    is_owner = (voter_session.voter_email == user_email)
    is_superadmin = (user_role == "superadmin" or user_role is True)
    if not (is_owner or is_superadmin):
        raise HTTPException(status_code=403, detail="Not authorized to view this session's leaderboard")
    # 3. Must be complete
    if not voter_session.is_complete:
        raise HTTPException(status_code=400, detail="Session not complete")
    # 4. Get options and match results
    options = await list_options_by_poll(poll_id=voter_session.poll_id, session=session)
    match_results = await list_match_results_by_session(session_id=session_id, session=session)
    from app.elo import process_session_elo
    elo_scores = process_session_elo(match_results=match_results, options=options)
    # 5. Build leaderboard entries
    entries = []
    for option, score in zip(options, elo_scores):
        entries.append({
            "label": option.label,
            "score": score,
            "option_id": str(option.id)  # TODO CHECK: Optionally remove if not needed
        })
    # 6. Sort and rank as in global leaderboard
    entries.sort(key=lambda x: (-x["score"]))
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
    return LeaderboardResponse(leaderboard=leaderboard) 