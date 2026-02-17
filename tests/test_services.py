"""
Unit tests for Dinero AI services.
Run with: pytest tests/ -v
"""
import pytest
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gst_classifier import classify_gst, get_gst_summary
from services.financial_engine import calculate_financials, assess_financial_health, get_overdue_clients
from utils.validators import validate_csv_structure, validate_data_types, sanitize_text_input, validate_month_label


class TestGSTClassifier:
    """Tests for GST classification engine."""
    
    def test_classify_software_expenses(self):
        """Test classification of software/cloud expenses."""
        assert "ITC Eligible - Software/Cloud" in classify_gst("AWS Cloud Subscription", 12000)
        assert "ITC Eligible - Software/Cloud" in classify_gst("Zoho Software", 5000)
        assert "ITC Eligible - Software/Cloud" in classify_gst("SaaS tools", 8000)
    
    def test_classify_professional_services(self):
        """Test classification of professional services."""
        assert "ITC Eligible - Professional Services" in classify_gst("CA Services", 15000)
        assert "ITC Eligible - Professional Services" in classify_gst("Legal fees", 10000)
        assert "ITC Eligible - Professional Services" in classify_gst("Consulting", 25000)
    
    def test_classify_capital_goods(self):
        """Test classification of capital goods."""
        assert "ITC Eligible - Capital Goods" in classify_gst("Laptop for employee", 65000)
        assert "ITC Eligible - Capital Goods" in classify_gst("Office furniture", 42000)
        assert "ITC Eligible - Capital Goods" in classify_gst("Printer and scanner", 18000)
    
    def test_classify_rent(self):
        """Test classification of rent expenses."""
        assert "ITC Eligible - Rent" in classify_gst("Office Rent", 20000)
        assert "ITC Eligible - Rent" in classify_gst("Monthly rent payment", 25000)
    
    def test_classify_travel(self):
        """Test classification of travel expenses."""
        # Hotel and flights are ITC eligible for business travel
        assert "ITC Eligible - Business Travel" in classify_gst("Hotel Stay Mumbai", 12000)
        assert "ITC Eligible - Business Travel" in classify_gst("Flight to Delhi", 9500)
        # Cab/taxi is blocked
        assert "Blocked Credit - Cab/Taxi" in classify_gst("Uber ride", 850)
        assert "Blocked Credit - Cab/Taxi" in classify_gst("Ola cab", 680)
    
    def test_classify_meals(self):
        """Test classification of meal expenses."""
        assert "Blocked Credit - Food/Meals" in classify_gst("Team Lunch", 2500)
        assert "Blocked Credit - Food/Meals" in classify_gst("Client dinner", 3800)
        assert "Blocked Credit - Food/Meals" in classify_gst("Swiggy order", 1850)
    
    def test_classify_utilities(self):
        """Test classification of utility expenses."""
        assert "ITC Eligible - Utilities" in classify_gst("Electricity Bill", 3000)
        assert "ITC Eligible - Utilities" in classify_gst("Internet Broadband", 1500)
        assert "ITC Eligible - Utilities" in classify_gst("Phone bill", 2800)
    
    def test_classify_maintenance(self):
        """Test classification of maintenance services."""
        assert "ITC Eligible - Maintenance" in classify_gst("Office cleaning", 2000)
        assert "ITC Eligible - Maintenance" in classify_gst("Security services", 8500)
        assert "ITC Eligible - Maintenance" in classify_gst("Pest control", 2800)
    
    def test_classify_training(self):
        """Test classification of training expenses."""
        assert "ITC Eligible - Training/Development" in classify_gst("Coursera training", 32000)
        assert "ITC Eligible - Training/Development" in classify_gst("Certification program", 45000)
        assert "ITC Eligible - Training/Development" in classify_gst("Workshop registration fee", 15000)
    
    def test_classify_marketing(self):
        """Test classification of marketing expenses."""
        assert "ITC Eligible - Marketing/Advertising" in classify_gst("Digital marketing campaign", 50000)
        assert "ITC Eligible - Marketing/Advertising" in classify_gst("Advertising", 25000)
    
    def test_classify_gifts_threshold(self):
        """Test gift classification based on threshold."""
        # Below threshold - needs review for tracking
        assert "Review Required" in classify_gst("Corporate gifts", 30000)
        # Above threshold - blocked
        assert "Blocked Credit - Gifts" in classify_gst("Executive gifts", 60000)
    
    def test_classify_review_required(self):
        """Test fallback to review required."""
        assert "Review Required" in classify_gst("Random payment", 5000)
        assert "Review Required" in classify_gst("Miscellaneous item", 3000)
    
    def test_classify_empty_description(self):
        """Test handling of empty/invalid descriptions."""
        assert "Review Required" in classify_gst("", 1000)
        assert "Review Required" in classify_gst(None, 1000)


class TestFinancialEngine:
    """Tests for financial calculations."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample ledger DataFrame."""
        return pd.DataFrame({
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "client": ["ABC Corp", "Vendor", "XYZ Ltd"],
            "description": ["Project work", "Office supplies", "Consulting"],
            "amount": [100000, 20000, 50000],
            "type": ["income", "expense", "income"],
            "status": ["paid", "paid", "unpaid"]
        })
    
    def test_calculate_revenue(self, sample_df):
        """Test revenue calculation."""
        metrics = calculate_financials(sample_df)
        assert metrics["revenue"] == 150000  # 100000 + 50000
    
    def test_calculate_expenses(self, sample_df):
        """Test expense calculation."""
        metrics = calculate_financials(sample_df)
        assert metrics["expenses"] == 20000
    
    def test_calculate_profit(self, sample_df):
        """Test profit calculation."""
        metrics = calculate_financials(sample_df)
        assert metrics["profit"] == 130000  # 150000 - 20000
    
    def test_calculate_receivables(self, sample_df):
        """Test receivables calculation."""
        metrics = calculate_financials(sample_df)
        assert metrics["receivables"] == 50000  # Only XYZ Ltd is unpaid
    
    def test_client_concentration(self, sample_df):
        """Test client concentration calculation."""
        metrics = calculate_financials(sample_df)
        # ABC Corp has 100000/150000 = 66.67%
        assert metrics["top_client_share"] > 60
        assert metrics["top_client_name"] == "ABC Corp"
    
    def test_assess_healthy_financials(self, sample_df):
        """Test health assessment for healthy business."""
        metrics = calculate_financials(sample_df)
        health = assess_financial_health(metrics)
        # Should have concentration risk but overall moderate/healthy
        assert health["score"] >= 50
    
    def test_get_overdue_clients(self, sample_df):
        """Test overdue client extraction."""
        overdue = get_overdue_clients(sample_df)
        assert "XYZ Ltd" in overdue
        assert "ABC Corp" not in overdue


class TestValidators:
    """Tests for input validation."""
    
    def test_validate_csv_structure_valid(self):
        """Test validation of valid CSV structure."""
        df = pd.DataFrame({
            "date": ["2026-01-01"],
            "client": ["ABC"],
            "description": ["Work"],
            "amount": [1000],
            "type": ["income"],
            "status": ["paid"]
        })
        is_valid, errors = validate_csv_structure(df)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_csv_structure_missing_columns(self):
        """Test validation with missing columns."""
        df = pd.DataFrame({
            "date": ["2026-01-01"],
            "amount": [1000]
        })
        is_valid, errors = validate_csv_structure(df)
        assert not is_valid
        assert len(errors) > 0
        assert "Missing required columns" in errors[0]
    
    def test_validate_data_types_valid(self):
        """Test data type validation for valid data."""
        df = pd.DataFrame({
            "type": ["income", "expense"],
            "status": ["paid", "unpaid"],
            "amount": [1000, 500]
        })
        is_valid, errors = validate_data_types(df)
        assert is_valid
    
    def test_validate_data_types_invalid_type(self):
        """Test data type validation with invalid type."""
        df = pd.DataFrame({
            "type": ["income", "invalid_type"],
            "status": ["paid", "unpaid"],
            "amount": [1000, 500]
        })
        is_valid, errors = validate_data_types(df)
        assert not is_valid
    
    def test_sanitize_text_input(self):
        """Test text sanitization."""
        # Test removal of script tags
        assert "<script>" not in sanitize_text_input("<script>alert('xss')</script>test")
        # Test truncation
        assert len(sanitize_text_input("a" * 1000, max_length=100)) == 100
        # Test normal text
        assert sanitize_text_input("Jan-2026") == "Jan-2026"
    
    def test_validate_month_label_valid(self):
        """Test month label validation for valid labels."""
        is_valid, error = validate_month_label("Jan-2026")
        assert is_valid
        
        is_valid, error = validate_month_label("January 2026")
        assert is_valid
    
    def test_validate_month_label_empty(self):
        """Test month label validation for empty input."""
        is_valid, error = validate_month_label("")
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_validate_month_label_too_long(self):
        """Test month label validation for too long input."""
        is_valid, error = validate_month_label("a" * 50)
        assert not is_valid
        assert "long" in error.lower()


class TestGSTSummary:
    """Tests for GST summary calculation."""
    
    def test_gst_summary_empty_df(self):
        """Test GST summary with empty DataFrame."""
        df = pd.DataFrame(columns=["amount", "gst_category"])
        summary = get_gst_summary(df)
        assert summary["total_expenses"] == 0
        assert summary["itc_eligible"] == 0
        assert summary["itc_health_score"] == 0
        assert summary["itc_health_status"] == "No Data"
    
    def test_gst_summary_calculation(self):
        """Test GST summary calculation with health score."""
        df = pd.DataFrame({
            "amount": [10000, 5000, 2000, 3000],
            "gst_category": [
                "ITC Eligible - Software/Cloud",
                "Blocked Credit - Food/Meals",
                "Review Required - Manual Classification Needed",
                "ITC Eligible - Professional Services"
            ]
        })
        summary = get_gst_summary(df)
        assert summary["total_expenses"] == 20000
        assert summary["itc_eligible"] == 13000  # 10000 + 3000
        assert summary["blocked_credit"] == 5000
        assert summary["review_required"] == 2000
        assert summary["itc_health_score"] == 65.0  # (13000/20000) * 100
        assert summary["itc_health_status"] == "Good"  # >60%
    
    def test_gst_health_status_moderate(self):
        """Test moderate ITC health status."""
        df = pd.DataFrame({
            "amount": [5000, 5000],
            "gst_category": [
                "ITC Eligible - Software/Cloud",
                "Blocked Credit - Food/Meals"
            ]
        })
        summary = get_gst_summary(df)
        assert summary["itc_health_score"] == 50.0
        assert summary["itc_health_status"] == "Moderate"
    
    def test_gst_health_status_needs_review(self):
        """Test needs review ITC health status."""
        df = pd.DataFrame({
            "amount": [3000, 7000],
            "gst_category": [
                "ITC Eligible - Software/Cloud",
                "Blocked Credit - Food/Meals"
            ]
        })
        summary = get_gst_summary(df)
        assert summary["itc_health_score"] == 30.0
        assert summary["itc_health_status"] == "Needs Review"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
