"""
Input Validation - Validates user inputs and data integrity.
Implements guardrails against invalid data and potential injection attacks.
"""
import pandas as pd
import re
from typing import Tuple, List, Optional
from config.settings import REQUIRED_COLUMNS, VALID_TYPES, VALID_STATUSES


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_csv_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that uploaded CSV has required structure.
    
    Args:
        df: Uploaded DataFrame
        
    Returns:
        Tuple of (is_valid, list of error messages)
    
    Example:
        >>> is_valid, errors = validate_csv_structure(df)
        >>> if not is_valid:
        ...     print("Validation errors:", errors)
    """
    errors = []
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Check for empty dataframe
    if df.empty:
        errors.append("Uploaded file is empty")
    
    return (len(errors) == 0, errors)


def validate_data_types(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate data types in the ledger.
    
    Args:
        df: Ledger DataFrame
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Validate 'type' column values
    if "type" in df.columns:
        invalid_types = df[~df["type"].isin(VALID_TYPES)]["type"].unique()
        if len(invalid_types) > 0:
            errors.append(f"Invalid transaction types: {', '.join(map(str, invalid_types))}. Expected: {', '.join(VALID_TYPES)}")
    
    # Validate 'status' column values
    if "status" in df.columns:
        invalid_statuses = df[~df["status"].isin(VALID_STATUSES)]["status"].unique()
        if len(invalid_statuses) > 0:
            errors.append(f"Invalid status values: {', '.join(map(str, invalid_statuses))}. Expected: {', '.join(VALID_STATUSES)}")
    
    # Validate amount is numeric
    if "amount" in df.columns:
        try:
            pd.to_numeric(df["amount"])
        except (ValueError, TypeError):
            errors.append("Amount column must contain numeric values")
    
    # Check for negative amounts
    if "amount" in df.columns:
        if (df["amount"] < 0).any():
            errors.append("Amount cannot be negative. Use 'type' column to indicate expense/income")
    
    return (len(errors) == 0, errors)


def sanitize_text_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize text input to prevent injection attacks and security issues.
    
    Args:
        text: Raw input text to be sanitized
        max_length: Maximum allowed length (default: 500 characters)
        
    Returns:
        Sanitized text with dangerous content removed
        
    Security measures applied:
        - Truncates to max_length
        - Removes HTML/XML tags
        - Removes JavaScript protocol handlers
        - Removes HTML event handlers (onclick, onerror, etc.)
        - Removes potentially dangerous special characters
        
    Example:
        >>> sanitize_text_input('<script>alert("xss")</script>Hello')
        'Hello'
        >>> sanitize_text_input('javascript:void(0)')
        'void(0)'
    """
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove potential script tags and dangerous content
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    # Remove special characters that could cause issues
    text = re.sub(r'[{}[\]\\|`~^]', '', text)
    
    return text.strip()


def validate_month_label(month_label: str) -> Tuple[bool, str]:
    """
    Validate month label format.
    
    Args:
        month_label: User-entered month label
        
    Returns:
        Tuple of (is_valid, error message or empty string)
    """
    if not month_label:
        return (False, "Month label cannot be empty")
    
    if len(month_label) > 20:
        return (False, "Month label too long (max 20 characters)")
    
    # Basic pattern check (allowing formats like "Jan-2026", "January 2026", "2026-01")
    if not re.match(r'^[a-zA-Z0-9\-\s]+$', month_label):
        return (False, "Month label contains invalid characters")
    
    return (True, "")


def validate_ledger(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Comprehensive ledger validation.
    
    Args:
        df: Ledger DataFrame
        
    Returns:
        Tuple of (is_valid, list of all error messages)
    """
    all_errors = []
    
    # Structure validation
    is_valid, errors = validate_csv_structure(df)
    all_errors.extend(errors)
    
    # If structure is invalid, skip data type validation
    if not is_valid:
        return (False, all_errors)
    
    # Data type validation
    _, errors = validate_data_types(df)
    all_errors.extend(errors)
    
    return (len(all_errors) == 0, all_errors)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize DataFrame.
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    
    # Lowercase type and status columns
    if "type" in df.columns:
        df["type"] = df["type"].str.lower()
    if "status" in df.columns:
        df["status"] = df["status"].str.lower()
    
    # Ensure amount is numeric
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors='coerce').fillna(0)
    
    return df
