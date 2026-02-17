"""
GST Classification Engine for Indian SMBs.
Classifies expenses into appropriate GST Input Tax Credit (ITC) categories.
"""
from config.settings import GST_CATEGORIES


def classify_gst(description: str) -> str:
    """
    Classify an expense into GST categories based on description.
    
    Args:
        description: The expense description text
        
    Returns:
        GST category string indicating ITC eligibility
    """
    if not description or not isinstance(description, str):
        return GST_CATEGORIES["REVIEW_REQUIRED"]
    
    desc = description.lower().strip()
    
    # Software/Cloud services - ITC Eligible
    software_keywords = ["aws", "software", "subscription", "cloud", "saas", 
                         "azure", "gcp", "hosting", "domain", "license"]
    if any(keyword in desc for keyword in software_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_SOFTWARE"]
    
    # Rent - ITC Eligible
    if "rent" in desc:
        return GST_CATEGORIES["ITC_ELIGIBLE_RENT"]
    
    # Travel - Non-Claimable
    travel_keywords = ["flight", "travel", "uber", "cab", "taxi", "ola", 
                       "railway", "train", "bus", "airfare"]
    if any(keyword in desc for keyword in travel_keywords):
        return GST_CATEGORIES["NON_CLAIMABLE_TRAVEL"]
    
    # Food/Meals - Blocked Credit
    food_keywords = ["food", "meal", "lunch", "dinner", "snacks", "breakfast",
                     "catering", "restaurant", "zomato", "swiggy"]
    if any(keyword in desc for keyword in food_keywords):
        return GST_CATEGORIES["BLOCKED_MEALS"]
    
    # Utilities - ITC Eligible
    utility_keywords = ["electricity", "internet", "wifi", "broadband", "phone",
                        "mobile", "telephone", "water", "gas"]
    if any(keyword in desc for keyword in utility_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_UTILITIES"]
    
    # Salaries - Not Applicable (no GST on salaries)
    salary_keywords = ["salary", "wages", "payroll", "bonus", "commission"]
    if any(keyword in desc for keyword in salary_keywords):
        return GST_CATEGORIES["NOT_APPLICABLE_SALARY"]
    
    # Office Supplies - ITC Eligible
    office_keywords = ["office", "supplies", "stationery", "furniture", 
                       "equipment", "computer", "laptop", "printer"]
    if any(keyword in desc for keyword in office_keywords):
        return GST_CATEGORIES["ITC_ELIGIBLE_OFFICE"]
    
    # Default - needs manual review
    return GST_CATEGORIES["REVIEW_REQUIRED"]


def get_gst_summary(gst_df) -> dict:
    """
    Generate GST summary statistics from expense dataframe.
    
    Args:
        gst_df: DataFrame with expenses and gst_category column
        
    Returns:
        Dictionary with ITC eligible amount, blocked amount, etc.
    """
    if gst_df.empty:
        return {
            "total_expenses": 0,
            "itc_eligible": 0,
            "blocked_credit": 0,
            "non_claimable": 0,
            "review_required": 0
        }
    
    summary = {
        "total_expenses": float(gst_df["amount"].sum()),
        "itc_eligible": 0,
        "blocked_credit": 0,
        "non_claimable": 0,
        "review_required": 0
    }
    
    for _, row in gst_df.iterrows():
        amount = float(row["amount"])
        category = row["gst_category"]
        
        if "ITC Eligible" in category:
            summary["itc_eligible"] += amount
        elif "Blocked" in category:
            summary["blocked_credit"] += amount
        elif "Non-Claimable" in category:
            summary["non_claimable"] += amount
        elif "Review Required" in category:
            summary["review_required"] += amount
    
    return summary
