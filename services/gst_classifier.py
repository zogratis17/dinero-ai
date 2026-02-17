"""
GST Classification Engine for Indian SMBs.
Classifies expenses into appropriate GST Input Tax Credit (ITC) categories.
Enhanced with comprehensive keyword matching based on GST Act provisions.
"""
from config.settings import GST_CATEGORIES
import re


def classify_gst(description: str, amount: float = 0) -> str:
    """
    Classify an expense into GST categories based on description and amount.
    Uses priority-based matching: specific categories first, then general.
    
    Args:
        description: The expense description text
        amount: Transaction amount (for threshold-based rules like gifts)
        
    Returns:
        GST category string indicating ITC eligibility
    """
    if not description or not isinstance(description, str):
        return GST_CATEGORIES["REVIEW_REQUIRED"]
    
    desc = description.lower().strip()
    
    # PRIORITY 1: Blocked Categories (Specific matches first)
    
    # Food/Meals - Blocked Credit
    food_keywords = ["food", "meal", "lunch", "dinner", "snacks", "breakfast",
                     "catering", "restaurant", "zomato", "swiggy", "domino",
                     "pizza", "burger", "cafe", "coffee", "tea", "beverages",
                     "pantry", "mcdonald", "kfc", "subway", "starbucks",
                     "dunkin", "haldiram", "uber eats"]
    if any(keyword in desc for keyword in food_keywords):
        return GST_CATEGORIES["BLOCKED_MEALS"]
    
    # Cab/Taxi - Blocked Transport
    cab_keywords = ["uber", "ola", "rapido", "cab", "taxi", "ride"]
    if any(keyword in desc for keyword in cab_keywords):
        return GST_CATEGORIES["BLOCKED_TRANSPORT"]
    
    # Salaries - Not Applicable (no GST on salaries)
    salary_keywords = ["salary", "wages", "payroll", "bonus", "commission"]
    if any(keyword in desc for keyword in salary_keywords):
        return GST_CATEGORIES["NOT_APPLICABLE_SALARY"]
    
    # Gifts - Check threshold (₹50,000 per person per year)
    gift_keywords = ["gift", "gifting", "corporate gift", "present"]
    if any(keyword in desc for keyword in gift_keywords):
        if amount > 50000:
            return GST_CATEGORIES["BLOCKED_GIFTS"]
        # Below threshold, gifts are eligible
        return GST_CATEGORIES["REVIEW_REQUIRED"]  # Needs tracking across year
    
    # Employee Benefits - Blocked
    employee_benefit_keywords = ["health insurance", "life insurance", "mediclaim",
                                 "gym", "fitness", "club membership", "wellness"]
    if any(keyword in desc for keyword in employee_benefit_keywords):
        return GST_CATEGORIES["BLOCKED_EMPLOYEE_BENEFITS"]
    
    # PRIORITY 2: Reverse Charge Mechanism
    
    rcm_keywords = ["advocate", "lawyer", "gta", "goods transport", "import of service",
                    "foreign service", "sponsorship", "unregistered vendor"]
    if any(keyword in desc for keyword in rcm_keywords):
        return GST_CATEGORIES["RCM_LIABLE"]
    
    # PRIORITY 3: ITC Eligible Categories
    
    # Professional Services - ITC Eligible
    professional_keywords = ["consulting", "consultant", "legal", "accounting",
                           "audit", "ca services", "chartered accountant", "tax",
                           "advisory", "freelancer", "professional", "compliance",
                           "background verification"]
    if any(keyword in desc for keyword in professional_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_PROFESSIONAL"]
    
    # Software/Cloud services - ITC Eligible
    software_keywords = ["aws", "software", "subscription", "cloud", "saas", 
                         "azure", "gcp", "hosting", "domain", "license",
                         "github", "gitlab", "atlassian", "jira", "confluence",
                         "slack", "zoom", "monday", "asana", "trello",
                         "zoho", "salesforce", "hubspot", "microsoft 365",
                         "office 365", "google workspace", "adobe", "figma",
                         "canva", "notion", "clickup", "postman", "vercel",
                         "heroku", "digitalocean", "cloudflare", "mongodb",
                         "firebase", "auth0", "okta", "twilio", "sendgrid",
                         "razorpay", "stripe", "payment gateway", "api",
                         "database", "cdn", "ssl", "certificate"]
    if any(keyword in desc for keyword in software_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_SOFTWARE"]
    
    # Capital Goods - ITC Eligible
    capital_keywords = ["laptop", "computer", "desktop", "server", "macbook",
                       "dell", "hp", "lenovo", "monitor", "screen", "keyboard",
                       "mouse", "printer", "scanner", "projector", "camera",
                       "furniture", "desk", "chair", "table", "cabinet",
                       "machinery", "equipment", "tool", "appliance",
                       "ac", "air conditioner", "refrigerator", "tv",
                       "conference", "network", "router", "switch",
                       "ups", "inverter", "generator"]
    if any(keyword in desc for keyword in capital_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_CAPITAL"]
    
    # Business Travel (Hotel/Flights) - ITC Eligible
    business_travel_keywords = ["hotel", "flight", "airline", "air india", "indigo",
                               "spicejet", "vistara", "emirates", "air asia",
                               "accommodation", "stay", "booking", "makemytrip",
                               "goibibo", "cleartrip", "conference", "summit",
                               "exhibition", "expo", "train" if "business" in desc else None]
    business_travel_keywords = [k for k in business_travel_keywords if k]  # Remove None
    if any(keyword in desc for keyword in business_travel_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_TRAVEL"]
    
    # Marketing/Advertising - ITC Eligible
    marketing_keywords = ["marketing", "advertising", "advertisement", "promotion",
                         "seo", "ppc", "adwords", "facebook ads", "google ads",
                         "social media", "branding", "design", "graphic",
                         "content", "copywriting", "campaign", "banner",
                         "hoarding", "digital marketing", "influencer"]
    if any(keyword in desc for keyword in marketing_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_MARKETING"]
    
    # Training/Development - ITC Eligible
    training_keywords = ["training", "course", "certification", "learning",
                        "coursera", "udemy", "udacity", "linkedin learning",
                        "skillshare", "pluralsight", "workshop", "seminar",
                        "conference registration", "nanodegree"]
    if any(keyword in desc for keyword in training_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_TRAINING"]
    
    # Maintenance Services - ITC Eligible
    maintenance_keywords = ["cleaning", "housekeeping", "maintenance", "repair",
                           "servicing", "amc", "annual maintenance", "pest control",
                           "fumigation", "security", "guard", "urban company"]
    if any(keyword in desc for keyword in maintenance_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_MAINTENANCE"]
    
    # Rent - ITC Eligible (Commercial)
    if "rent" in desc or "co-working" in desc or "wework" in desc:
        return GST_CATEGORIES["ITC_ELIGIBLE_RENT"]
    
    # Utilities - ITC Eligible
    utility_keywords = ["electricity", "bescom", "power", "internet", "wifi",
                       "broadband", "phone", "mobile", "telephone", "airtel",
                       "jio", "vodafone", "bsnl", "act fibernet", "tata sky",
                       "dth", "communication"]
    if any(keyword in desc for keyword in utility_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_UTILITIES"]
    
    # Office Supplies - ITC Eligible
    office_keywords = ["office supplies", "stationery", "paper", "pen", "pencil",
                      "notebook", "file", "folder", "supplies", "amazon" if "office" in desc else None,
                      "flipkart" if "office" in desc else None]
    office_keywords = [k for k in office_keywords if k]  # Remove None
    if any(keyword in desc for keyword in office_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_OFFICE"]
    
    # Business Insurance - ITC Eligible
    insurance_keywords = ["insurance" if any(x in desc for x in ["property", "business", "liability", "professional", "cyber"]) else None]
    insurance_keywords = [k for k in insurance_keywords if k]  # Remove None
    if insurance_keywords:
        return GST_CATEGORIES["ITC_ELIGIBLE_INSURANCE"]
    
    # Banking/Payment Services - ITC Eligible
    banking_keywords = ["payment gateway", "razorpay", "paytm", "merchant",
                       "transaction fee", "gateway"]
    if any(keyword in desc for keyword in banking_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_BANKING"]
    
    # PRIORITY 4: Check for common vendor patterns
    eligible_vendors = ["aws", "microsoft", "google", "adobe", "github",
                       "linkedin", "naukri", "indeed", "freelancer"]
    if any(vendor in desc for vendor in eligible_vendors):
        return GST_CATEGORIES["ITC_ELIGIBLE_SOFTWARE"]
    
    # Default - needs manual review
    return GST_CATEGORIES["REVIEW_REQUIRED"]


def get_gst_summary(gst_df) -> dict:
    """
    Generate GST summary statistics from expense dataframe.
    Enhanced with ITC health score and detailed breakdowns.
    
    Args:
        gst_df: DataFrame with expenses and gst_category column
        
    Returns:
        Dictionary with ITC eligible amount, blocked amount, health score, etc.
    """
    if gst_df.empty:
        return {
            "total_expenses": 0,
            "itc_eligible": 0,
            "blocked_credit": 0,
            "non_applicable": 0,
            "review_required": 0,
            "rcm_liable": 0,
            "itc_health_score": 0,
            "itc_health_status": "No Data"
        }
    
    summary = {
        "total_expenses": float(gst_df["amount"].sum()),
        "itc_eligible": 0,
        "blocked_credit": 0,
        "non_applicable": 0,
        "review_required": 0,
        "rcm_liable": 0
    }
    
    for _, row in gst_df.iterrows():
        amount = float(row["amount"])
        category = row["gst_category"]
        
        if "ITC Eligible" in category:
            summary["itc_eligible"] += amount
        elif "Blocked" in category:
            summary["blocked_credit"] += amount
        elif "Not Applicable" in category or "Exempt" in category:
            summary["non_applicable"] += amount
        elif "Review Required" in category:
            summary["review_required"] += amount
        elif "Reverse Charge" in category:
            summary["rcm_liable"] += amount
            summary["itc_eligible"] += amount  # RCM is eligible after paying tax
    
    # Calculate ITC Health Score
    if summary["total_expenses"] > 0:
        itc_percentage = (summary["itc_eligible"] / summary["total_expenses"]) * 100
        summary["itc_health_score"] = round(itc_percentage, 2)
        
        # Determine health status
        if itc_percentage >= 60:
            summary["itc_health_status"] = "Good"
        elif itc_percentage >= 40:
            summary["itc_health_status"] = "Moderate"
        else:
            summary["itc_health_status"] = "Needs Review"
    else:
        summary["itc_health_score"] = 0
        summary["itc_health_status"] = "No Data"
    
    return summary


def calculate_potential_itc_savings(blocked_amount: float, gst_rate: float = 18) -> float:
    """
    Calculate potential ITC savings if blocked expenses were reclassified.
    
    Args:
        blocked_amount: Total amount in blocked credit category
        gst_rate: Applicable GST rate (default 18%)
        
    Returns:
        Potential GST credit amount
    """
    return (blocked_amount * gst_rate) / (100 + gst_rate)
