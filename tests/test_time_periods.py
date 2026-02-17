"""
Tests for time-based data segmentation and analysis.
Run with: pytest tests/test_time_periods.py -v
"""
import pytest
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.time_periods import (
    segment_by_period, get_period_metrics, compare_periods,
    get_available_periods, format_period_label, get_trend_direction
)


class TestSegmentByPeriod:
    """Tests for period segmentation."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample ledger with various dates."""
        return pd.DataFrame({
            "date": [
                "2026-01-01", "2026-01-05", "2026-01-15",
                "2026-02-01", "2026-02-10",
                "2026-03-01", "2026-03-15"
            ],
            "client": ["ABC", "DEF", "GHI", "ABC", "JKL", "MNO", "PQR"],
            "description": ["Work", "Work", "Work", "Work", "Work", "Work", "Work"],
            "amount": [10000, 15000, 20000, 12000, 18000, 14000, 16000],
            "type": ["income"] * 7,
            "status": ["paid"] * 7
        })
    
    def test_segment_by_month(self, sample_df):
        """Test monthly segmentation."""
        segments = segment_by_period(sample_df, 'month')
        
        assert "2026-01" in segments
        assert "2026-02" in segments
        assert "2026-03" in segments
        assert len(segments["2026-01"]) == 3
        assert len(segments["2026-02"]) == 2
        assert len(segments["2026-03"]) == 2
    
    def test_segment_by_week(self, sample_df):
        """Test weekly segmentation."""
        segments = segment_by_period(sample_df, 'week')
        
        # Should have multiple weeks
        assert len(segments) > 0
        # Each segment should be a DataFrame
        for period, df in segments.items():
            assert isinstance(df, pd.DataFrame)
    
    def test_segment_by_day(self, sample_df):
        """Test daily segmentation."""
        segments = segment_by_period(sample_df, 'day')
        
        assert "2026-01-01" in segments
        assert "2026-01-05" in segments
        assert len(segments["2026-01-01"]) == 1
    
    def test_segment_by_year(self, sample_df):
        """Test yearly segmentation."""
        segments = segment_by_period(sample_df, 'year')
        
        assert "2026" in segments
        assert len(segments["2026"]) == 7
    
    def test_segment_invalid_period(self, sample_df):
        """Test that invalid period raises error."""
        with pytest.raises(ValueError):
            segment_by_period(sample_df, 'invalid')
    
    def test_segment_empty_dataframe(self):
        """Test segmentation with empty DataFrame."""
        empty_df = pd.DataFrame({"date": []})
        segments = segment_by_period(empty_df, 'month')
        assert len(segments) == 0
    
    def test_segment_no_date_column(self):
        """Test segmentation without date column."""
        df = pd.DataFrame({"amount": [100, 200]})
        segments = segment_by_period(df, 'month')
        assert len(segments) == 0


class TestGetAvailablePeriods:
    """Tests for retrieving available periods."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample ledger."""
        return pd.DataFrame({
            "date": ["2026-01-01", "2026-01-15", "2026-02-01", "2026-03-10"],
            "amount": [100, 200, 300, 400],
            "type": ["income"] * 4
        })
    
    def test_get_available_months(self, sample_df):
        """Test getting available months."""
        months = get_available_periods(sample_df, 'month')
        
        assert "2026-01" in months
        assert "2026-02" in months
        assert "2026-03" in months
        assert len(months) == 3
    
    def test_periods_are_sorted(self, sample_df):
        """Test that periods are sorted."""
        months = get_available_periods(sample_df, 'month')
        
        assert months == sorted(months)
    
    def test_get_available_days(self, sample_df):
        """Test getting available days."""
        days = get_available_periods(sample_df, 'day')
        
        assert "2026-01-01" in days
        assert "2026-01-15" in days
        assert len(days) == 4
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame({"date": []})
        periods = get_available_periods(empty_df, 'month')
        
        assert len(periods) == 0


class TestFormatPeriodLabel:
    """Tests for period label formatting."""
    
    def test_format_month_label(self):
        """Test formatting of month labels."""
        formatted = format_period_label("2026-01", "month")
        assert "January" in formatted
        assert "2026" in formatted
    
    def test_format_day_label(self):
        """Test formatting of day labels."""
        formatted = format_period_label("2026-01-15", "day")
        assert "15" in formatted
        assert "2026" in formatted
    
    def test_format_year_label(self):
        """Test formatting of year label."""
        formatted = format_period_label("2026", "year")
        assert "2026" in formatted
    
    def test_format_week_label(self):
        """Test formatting of week label."""
        formatted = format_period_label("2026-W05", "week")
        assert "Week" in formatted or "05" in formatted
    
    def test_invalid_format_returns_key(self):
        """Test that invalid formats return original key."""
        result = format_period_label("invalid-date", "month")
        assert result == "invalid-date" or len(result) > 0


class TestComparePeriods:
    """Tests for period comparison."""
    
    def test_compare_periods_growth(self):
        """Test comparison showing growth."""
        current = {
            "revenue": 150000,
            "expenses": 50000,
            "profit": 100000,
            "receivables": 30000,
            "profit_margin": 66.7
        }
        
        previous = {
            "revenue": 100000,
            "expenses": 40000,
            "profit": 60000,
            "receivables": 20000,
            "profit_margin": 60.0
        }
        
        comparison = compare_periods(current, previous)
        
        assert comparison["revenue_change"] == 50000
        assert comparison["revenue_pct_change"] == 50.0
        assert comparison["profit_change"] == 40000
        assert comparison["expenses_change"] == 10000
    
    def test_compare_periods_decline(self):
        """Test comparison showing decline."""
        current = {
            "revenue": 80000,
            "expenses": 50000,
            "profit": 30000,
            "receivables": 40000,
            "profit_margin": 37.5
        }
        
        previous = {
            "revenue": 100000,
            "expenses": 40000,
            "profit": 60000,
            "receivables": 20000,
            "profit_margin": 60.0
        }
        
        comparison = compare_periods(current, previous)
        
        assert comparison["revenue_change"] == -20000
        assert comparison["revenue_pct_change"] == -20.0
        assert comparison["profit_change"] == -30000
    
    def test_compare_periods_zero_previous(self):
        """Test comparison with zero previous values."""
        current = {"revenue": 100000, "expenses": 0, "profit": 0, "receivables": 0, "profit_margin": 0}
        previous = {"revenue": 0, "expenses": 0, "profit": 0, "receivables": 0, "profit_margin": 0}
        
        comparison = compare_periods(current, previous)
        
        assert comparison["revenue_pct_change"] == 100


class TestGetTrendDirection:
    """Tests for trend direction detection."""
    
    def test_trend_up(self):
        """Test upward trend detection."""
        comparison = {"revenue_pct_change": 15}
        direction = get_trend_direction(comparison, "revenue")
        assert direction == "up"
    
    def test_trend_down(self):
        """Test downward trend detection."""
        comparison = {"revenue_pct_change": -10}
        direction = get_trend_direction(comparison, "revenue")
        assert direction == "down"
    
    def test_trend_stable(self):
        """Test stable trend detection."""
        comparison = {"revenue_pct_change": 2}
        direction = get_trend_direction(comparison, "revenue")
        assert direction == "stable"
    
    def test_trend_zero(self):
        """Test zero change is stable."""
        comparison = {"revenue_pct_change": 0}
        direction = get_trend_direction(comparison, "revenue")
        assert direction == "stable"


class TestPeriodMetrics:
    """Tests for period metrics calculation."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample ledger."""
        return pd.DataFrame({
            "date": ["2026-01-01", "2026-01-05"],
            "amount": [100000, 50000],
            "type": ["income", "income"],
            "client": ["ABC", "DEF"],
            "description": ["Work", "Work"],
            "status": ["paid", "paid"]
        })
    
    def test_period_metrics_includes_period_label(self, sample_df):
        """Test that metrics include period label."""
        metrics = get_period_metrics(sample_df, "2026-01")
        
        assert metrics["period"] == "2026-01"
        assert "transaction_count" in metrics
        assert metrics["transaction_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
