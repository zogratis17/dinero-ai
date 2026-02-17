"""
Application configuration and constants.
Centralizes all configurable parameters for easy maintenance.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ----------------------------
# API Configuration
# ----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "models/gemini-2.5-flash"

# ----------------------------
# File Paths
# ----------------------------
MEMORY_DIR = "memory"
MEMORY_FILE = os.path.join(MEMORY_DIR, "financial_history.json")

# ----------------------------
# Business Rules & Thresholds
# ----------------------------
# Receivables threshold (percentage of revenue)
HIGH_RECEIVABLES_THRESHOLD = 0.3  # 30%

# Client concentration risk threshold
CLIENT_CONCENTRATION_THRESHOLD = 50  # 50%

# Maximum retries for API calls
MAX_API_RETRIES = 3
API_RETRY_DELAY = 2  # seconds

# ----------------------------
# GST Categories
# ----------------------------
GST_CATEGORIES = {
    "ITC_ELIGIBLE_SOFTWARE": "ITC Eligible - Software/Cloud",
    "ITC_ELIGIBLE_RENT": "ITC Eligible - Rent",
    "ITC_ELIGIBLE_UTILITIES": "ITC Eligible - Utilities",
    "ITC_ELIGIBLE_OFFICE": "ITC Eligible - Office Supplies",
    "NON_CLAIMABLE_TRAVEL": "Non-Claimable - Travel",
    "BLOCKED_MEALS": "Blocked Credit - Meals",
    "NOT_APPLICABLE_SALARY": "Not Applicable - Salaries",
    "REVIEW_REQUIRED": "Review Required"
}

# ----------------------------
# Required CSV Columns
# ----------------------------
REQUIRED_COLUMNS = ["date", "client", "description", "amount", "type", "status"]
VALID_TYPES = ["income", "expense"]
VALID_STATUSES = ["paid", "unpaid"]

# ----------------------------
# UI Configuration
# ----------------------------
PAGE_TITLE = "Dinero AI Agent"
PAGE_LAYOUT = "wide"
