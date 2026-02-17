"""
Application configuration and constants.
Centralizes all configurable parameters for easy maintenance.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Validate critical configuration
if not os.getenv("GEMINI_API_KEY") and os.getenv("USE_OLLAMA", "false").lower() != "true":
    import warnings
    warnings.warn(
        "GEMINI_API_KEY not found in environment. AI features will be unavailable. "
        "Please add GEMINI_API_KEY to your .env file or set USE_OLLAMA=true.",
        UserWarning
    )

# ----------------------------
# Feature Flags
# ----------------------------
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"

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
# AI Configuration
# ----------------------------
# Google Gemini (Default)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "models/gemini-2.5-flash"

# Ollama (Alternative)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

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
# GST Categories (Expanded)
# ----------------------------
GST_CATEGORIES = {
    # ITC Eligible Categories
    "ITC_ELIGIBLE_SOFTWARE": "ITC Eligible - Software/Cloud",
    "ITC_ELIGIBLE_PROFESSIONAL": "ITC Eligible - Professional Services",
    "ITC_ELIGIBLE_RENT": "ITC Eligible - Rent (Commercial)",
    "ITC_ELIGIBLE_UTILITIES": "ITC Eligible - Utilities",
    "ITC_ELIGIBLE_OFFICE": "ITC Eligible - Office Supplies",
    "ITC_ELIGIBLE_CAPITAL": "ITC Eligible - Capital Goods",
    "ITC_ELIGIBLE_MAINTENANCE": "ITC Eligible - Maintenance Services",
    "ITC_ELIGIBLE_MARKETING": "ITC Eligible - Marketing/Advertising",
    "ITC_ELIGIBLE_TRAVEL": "ITC Eligible - Business Travel",
    "ITC_ELIGIBLE_TRAINING": "ITC Eligible - Training/Development",
    "ITC_ELIGIBLE_INSURANCE": "ITC Eligible - Business Insurance",
    "ITC_ELIGIBLE_BANKING": "ITC Eligible - Payment Services",
    
    # Blocked Credit Categories
    "BLOCKED_MEALS": "Blocked Credit - Food/Meals",
    "BLOCKED_TRANSPORT": "Blocked Credit - Cab/Taxi",
    "BLOCKED_EMPLOYEE_BENEFITS": "Blocked Credit - Employee Benefits",
    "BLOCKED_GIFTS": "Blocked Credit - Gifts (Above Threshold)",
    
    # Special Categories
    "RCM_LIABLE": "Reverse Charge Mechanism",
    "NOT_APPLICABLE_SALARY": "Not Applicable - Salaries",
    "EXEMPT_SUPPLY": "Exempt from GST",
    "REVIEW_REQUIRED": "Review Required - Manual Classification Needed"
}

# GST ITC Health Score Thresholds
GST_ITC_HEALTH_GOOD = 60  # >60% ITC eligible is good
GST_ITC_HEALTH_MODERATE = 40  # 40-60% is moderate

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
