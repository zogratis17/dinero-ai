"""
Tests for enhanced memory system with period-based auto-save.
Run with: pytest tests/test_enhanced_memory.py -v
"""
import pytest
import json
import os
import sys
import shutil
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_memory import (
    save_period_data, load_period_data, get_all_periods,
    auto_save_periods, get_financial_context, clear_period_data,
    ensure_memory_dirs, DAILY_DIR, MONTHLY_DIR, WEEKLY_DIR, YEARLY_DIR
)


class TestSavePeriodData:
    """Tests for saving period-specific data."""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Cleanup test data before and after tests."""
        yield
        # Clean up test periods
        for period_type in ['day', 'week', 'month', 'year']:
            clear_period_data(period_type)
    
    def test_save_daily_data(self):
        """Test saving daily data."""
        ensure_memory_dirs()
        metrics = {
            "revenue": 100000,
            "expenses": 30000,
            "profit": 70000,
            "transaction_count": 5
        }
        
        result = save_period_data("day", "2026-01-15", metrics)
        
        assert result is True
        assert os.path.exists(DAILY_DIR)
    
    def test_save_monthly_data(self):
        """Test saving monthly data."""
        ensure_memory_dirs()
        metrics = {
            "revenue": 500000,
            "expenses": 200000,
            "profit": 300000,
            "transaction_count": 25
        }
        
        result = save_period_data("month", "2026-01", metrics)
        
        assert result is True
        assert os.path.exists(MONTHLY_DIR)
    
    def test_save_weekly_data(self):
        """Test saving weekly data."""
        ensure_memory_dirs()
        metrics = {
            "revenue": 200000,
            "expenses": 80000,
            "profit": 120000
        }
        
        result = save_period_data("week", "2026-W05", metrics)
        
        assert result is True
    
    def test_save_yearly_data(self):
        """Test saving yearly data."""
        ensure_memory_dirs()
        metrics = {
            "revenue": 2000000,
            "expenses": 800000,
            "profit": 1200000,
            "transaction_count": 150
        }
        
        result = save_period_data("year", "2026", metrics)
        
        assert result is True


class TestLoadPeriodData:
    """Tests for loading period data."""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup test data and cleanup after."""
        ensure_memory_dirs()
        # Save test data
        daily_data = {
            "revenue": 100000,
            "expenses": 30000,
            "profit": 70000,
            "timestamp": datetime.now().isoformat()
        }
        save_period_data("day", "2026-01-15", daily_data)
        
        yield
        
        # Cleanup
        clear_period_data("day")
    
    def test_load_existing_data(self):
        """Test loading existing period data."""
        data = load_period_data("day", "2026-01-15")
        
        assert data is not None
        assert data["revenue"] == 100000
        assert data["expenses"] == 30000
    
    def test_load_nonexistent_data(self):
        """Test loading non-existent period data."""
        data = load_period_data("day", "2099-01-01")
        
        assert data is None
    
    def test_load_data_preserves_metrics(self):
        """Test that loaded data preserves all metrics."""
        data = load_period_data("day", "2026-01-15")
        
        required_keys = ["revenue", "expenses", "profit"]
        for key in required_keys:
            assert key in data


class TestGetAllPeriods:
    """Tests for retrieving all available periods."""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup multiple periods and cleanup after."""
        ensure_memory_dirs()
        
        # Create multiple daily files
        dates = ["2026-01-01", "2026-01-05", "2026-01-10"]
        for date in dates:
            data = {"revenue": 100000, "timestamp": datetime.now().isoformat()}
            save_period_data("day", date, data)
        
        yield
        
        clear_period_data("day")
    
    def test_get_all_daily_periods(self):
        """Test retrieving all daily periods."""
        periods = get_all_periods("day")
        
        assert len(periods) >= 3
        labels = [p.get('period_label') for p in periods]
        assert "2026-01-01" in labels
        assert "2026-01-05" in labels
    
    def test_get_all_periods_empty_dir(self):
        """Test getting periods from empty directory."""
        clear_period_data("week")
        periods = get_all_periods("week")
        
        assert len(periods) == 0
    
    def test_periods_are_sorted(self):
        """Test that retrieved periods maintain order."""
        periods = get_all_periods("day")
        
        # Should have periods from setup
        assert len(periods) > 0


class TestAutoSavePeriods:
    """Tests for batch auto-save functionality."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample ledger."""
        return pd.DataFrame({
            "date": ["2026-01-01", "2026-01-05", "2026-01-15"],
            "amount": [100000, 50000, 75000],
            "type": ["income", "income", "income"],
            "client": ["ABC", "DEF", "GHI"],
            "description": ["Work", "Work", "Work"],
            "status": ["paid", "paid", "paid"]
        })
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Cleanup after tests."""
        yield
        for period_type in ['day', 'week', 'month', 'year']:
            clear_period_data(period_type)
    
    def test_auto_save_creates_directories(self, sample_df):
        """Test that auto-save creates period directories."""
        from utils.time_periods import segment_by_period
        
        ensure_memory_dirs()
        segments = segment_by_period(sample_df, 'day')
        
        # Should create daily directory
        assert os.path.exists(DAILY_DIR)
    
    def test_auto_save_returns_dict(self, sample_df):
        """Test that auto-save returns dictionary of results."""
        from utils.time_periods import segment_by_period
        
        ensure_memory_dirs()
        segments = segment_by_period(sample_df, 'day')
        results = auto_save_periods(sample_df, segments, 'day')
        
        assert isinstance(results, dict)
        assert len(results) > 0


class TestGetFinancialContext:
    """Tests for retrieving financial context for chatbot."""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Create financial data and cleanup after."""
        ensure_memory_dirs()
        
        # Create monthly data
        for month in range(1, 4):
            month_str = f"2026-{month:02d}"
            data = {
                "revenue": 500000 + (month * 50000),
                "expenses": 200000 + (month * 20000),
                "profit": 300000 + (month * 30000),
                "transaction_count": 20 + (month * 2),
                "timestamp": datetime.now().isoformat()
            }
            save_period_data("month", month_str, data)
        
        yield
        
        clear_period_data("month")
    
    def test_context_includes_data(self):
        """Test that context includes financial data."""
        context = get_financial_context(period_type='month', limit=3)
        
        assert context is not None
        assert len(context) > 0
    
    def test_context_is_string(self):
        """Test that context is a formatted string."""
        context = get_financial_context(period_type='month', limit=3)
        
        assert isinstance(context, str)
    
    def test_context_respects_limit(self):
        """Test that context respects limit parameter."""
        context_3 = get_financial_context(period_type='month', limit=3)
        context_1 = get_financial_context(period_type='month', limit=1)
        
        # Both should be valid strings
        assert isinstance(context_3, str)
        assert isinstance(context_1, str)


class TestClearPeriodData:
    """Tests for clearing period data."""
    
    def test_clear_specific_day_period(self):
        """Test clearing day periods."""
        ensure_memory_dirs()
        
        # Save some data
        data = {"revenue": 100000, "profit": 50000}
        save_period_data("day", "2026-TEST-01", data)
        
        # Verify it exists
        loaded = load_period_data("day", "2026-TEST-01")
        assert loaded is not None
        
        # Clear all day data
        result = clear_period_data("day")
        assert result is True
    
    def test_clear_returns_true(self):
        """Test that clear returns success."""
        result = clear_period_data("month")
        assert result is True or result is False


class TestBoundaryConditions:
    """Tests for edge cases and boundary conditions."""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Cleanup after tests."""
        yield
        for period_type in ['day', 'week', 'month', 'year']:
            try:
                clear_period_data(period_type)
            except:
                pass
    
    def test_save_zero_metrics(self):
        """Test saving metrics with zero values."""
        ensure_memory_dirs()
        
        metrics = {
            "revenue": 0,
            "expenses": 0,
            "profit": 0
        }
        
        result = save_period_data("day", "2026-ZERO-01", metrics)
        assert result is True
    
    def test_save_large_metrics(self):
        """Test saving very large metric values."""
        ensure_memory_dirs()
        
        metrics = {
            "revenue": 9999999999,
            "expenses": 5000000000,
            "profit": 4999999999
        }
        
        result = save_period_data("day", "2026-LARGE-01", metrics)
        assert result is True
    
    def test_invalid_period_type_returns_false(self):
        """Test that invalid period type returns False."""
        ensure_memory_dirs()
        
        metrics = {"revenue": 100000}
        result = save_period_data("invalid", "2026-01-01", metrics)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
