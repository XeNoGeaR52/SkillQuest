"""
Unit tests for XP service functions.
"""
import pytest
from app.services.xp_service import (
    calculate_xp_awarded,
    calculate_level,
    calculate_next_level_xp,
    is_passing_score
)


class TestXPCalculation:
    """Test XP calculation functions."""

    def test_calculate_xp_awarded_full_score(self):
        """Test XP calculation with 100% score."""
        result = calculate_xp_awarded(100, 100)
        assert result == 100

    def test_calculate_xp_awarded_partial_score(self):
        """Test XP calculation with partial score."""
        result = calculate_xp_awarded(100, 75)
        assert result == 75

    def test_calculate_xp_awarded_zero_score(self):
        """Test XP calculation with 0% score."""
        result = calculate_xp_awarded(100, 0)
        assert result == 0

    def test_calculate_xp_awarded_rounding(self):
        """Test XP calculation with rounding."""
        result = calculate_xp_awarded(100, 33.333)
        assert result == 33  # Should round down


class TestLevelCalculation:
    """Test level calculation functions."""

    def test_calculate_level_zero_xp(self):
        """Test level calculation with 0 XP."""
        assert calculate_level(0) == 1

    def test_calculate_level_100_xp(self):
        """Test level calculation with 100 XP."""
        assert calculate_level(100) == 2

    def test_calculate_level_400_xp(self):
        """Test level calculation with 400 XP."""
        assert calculate_level(400) == 3

    def test_calculate_level_900_xp(self):
        """Test level calculation with 900 XP."""
        assert calculate_level(900) == 4

    def test_calculate_level_1600_xp(self):
        """Test level calculation with 1600 XP."""
        assert calculate_level(1600) == 5

    def test_calculate_next_level_xp_level_1(self):
        """Test next level XP for level 1."""
        assert calculate_next_level_xp(1) == 100

    def test_calculate_next_level_xp_level_2(self):
        """Test next level XP for level 2."""
        assert calculate_next_level_xp(2) == 400

    def test_calculate_next_level_xp_level_3(self):
        """Test next level XP for level 3."""
        assert calculate_next_level_xp(3) == 900


class TestPassingScore:
    """Test passing score determination."""

    def test_is_passing_score_exact_threshold(self):
        """Test exact threshold score."""
        assert is_passing_score(70.0) is True

    def test_is_passing_score_above_threshold(self):
        """Test score above threshold."""
        assert is_passing_score(85.0) is True

    def test_is_passing_score_below_threshold(self):
        """Test score below threshold."""
        assert is_passing_score(69.9) is False

    def test_is_passing_score_custom_threshold(self):
        """Test with custom threshold."""
        assert is_passing_score(80.0, threshold=80.0) is True
        assert is_passing_score(79.9, threshold=80.0) is False
