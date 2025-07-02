from typing import List, Tuple
import math
from app.models import MatchResult, Option

def elo_probability(rating_a: float, rating_b: float) -> float:
    """Calculate the expected probability of A beating B."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))

def elo_update(
    rating_a: float, rating_b: float, winner: int, k: float = 32.0
) -> Tuple[float, float]:
    """Update Elo ratings for a match. Winner: 0 for A, 1 for B."""
    expected_a = elo_probability(rating_a, rating_b)
    expected_b = 1.0 - expected_a
    score_a = 1.0 if winner == 0 else 0.0
    score_b = 1.0 - score_a
    new_a = rating_a + k * (score_a - expected_a)
    new_b = rating_b + k * (score_b - expected_b)
    return new_a, new_b

def k_decay(k_base: float, match_number: int) -> float:
    """Decay K by match number (1-based)."""
    return k_base / math.sqrt(match_number)

def mean_center(scores: List[float]) -> List[float]:
    """Mean-center a list of scores."""
    mean = sum(scores) / len(scores) if scores else 0.0
    return [s - mean for s in scores]

def process_session_elo(match_results: List[MatchResult], options: List[Option]) -> List[float]:]
    # TODO: think of the security imporvements that could be made around this.
    """
    Process all match results for a session and return final Elo scores for all options.
    
    Args:
        match_results: List of match results for the session
        options: List of all options in the poll
    
    Returns:
        List of final Elo scores for all options (in same order as options)
    """
    # Initialize all options with same starting Elo rating
    initial_rating = 500.0
    option_ratings = {option.id: initial_rating for option in options}
    
    # Process each match result in order
    for i, match in enumerate(match_results):
        # Get current ratings for winner and loser
        winner_rating = option_ratings[match.winner_option_id]
        loser_rating = option_ratings[match.loser_option_id]
        
        # Calculate K with decay
        k = k_decay(32.0, i + 1)
        
        # Update Elo ratings (winner is option A, loser is option B)
        new_winner_rating, new_loser_rating = elo_update(
            winner_rating, loser_rating, winner=0, k=k
        )
        
        # Update the ratings
        option_ratings[match.winner_option_id] = new_winner_rating
        option_ratings[match.loser_option_id] = new_loser_rating
    
    # Return final ratings in the same order as options
    return [option_ratings[option.id] for option in options] 