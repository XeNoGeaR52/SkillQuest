import math


def calculate_xp_awarded(challenge_xp: int, score: float) -> int:
    """
    Calculate XP awarded based on challenge XP and user's score.

    Args:
        challenge_xp: Base XP for the challenge
        score: User's score (0-100)

    Returns:
        XP to award (rounded)
    """
    return round(challenge_xp * (score / 100))


def calculate_level(total_xp: int) -> int:
    """
    Calculate user level based on total XP.

    Formula: level = floor(sqrt(total_xp / 100)) + 1

    Args:
        total_xp: User's total XP

    Returns:
        User's level
    """
    if total_xp <= 0:
        return 1
    return int(math.sqrt(total_xp / 100)) + 1


def calculate_next_level_xp(current_level: int) -> int:
    """
    Calculate XP required for the next level.

    Args:
        current_level: User's current level

    Returns:
        Total XP required to reach next level
    """
    # Inverse of the level formula: xp = ((level - 1) ^ 2) * 100
    next_level = current_level + 1
    return ((next_level - 1) ** 2) * 100


def is_passing_score(score: float, threshold: float = 70.0) -> bool:
    """
    Determine if a score is passing.

    Args:
        score: The score to check
        threshold: Minimum passing score (default: 70.0)

    Returns:
        True if passing, False otherwise
    """
    return score >= threshold
