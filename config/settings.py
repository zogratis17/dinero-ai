"""
Application configuration and constants.
Centralizes all configurable parameters for easy maintenance.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ----------------------------
# Feature Flags
# ----------------------------
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

# ----------------------------
# Database Configuration
# ----------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://dinero_user:dinero_pass@localhost:5432/dinero_ai"
)

# Connection pool settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

# ----------------------------
# AI Configuration (Local LLM Backend)
# ----------------------------
# URL of the Flask LLM service (backend_llm_api/llm_service.py)
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:8000")

# API key for authenticating with the LLM backend
LLM_API_KEY = os.getenv("LLM_API_KEY", "prod_secret_key_123")

# Request timeout for LLM calls (seconds) — local models can be slow
LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "120"))

# ----------------------------
# File Paths (Legacy JSON Storage)
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
