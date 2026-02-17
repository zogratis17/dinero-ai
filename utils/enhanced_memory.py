"""
Enhanced financial memory system with time-based storage.
Automatically saves and retrieves financial data by day, week, month, year.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DIR = "memory"
HISTORY_FILE = os.path.join(MEMORY_DIR, "financial_history.json")
MONTHLY_DIR = os.path.join(MEMORY_DIR, "monthly")
WEEKLY_DIR = os.path.join(MEMORY_DIR, "weekly")
DAILY_DIR = os.path.join(MEMORY_DIR, "daily")
YEARLY_DIR = os.path.join(MEMORY_DIR, "yearly")


def ensure_memory_dirs() -> None:
    """Create all memory directories if they don't exist.
    
    Creates the following directory structure:
    - memory/                (main directory)
    - memory/monthly/        (monthly aggregated data)
    - memory/weekly/         (weekly aggregated data)
    - memory/daily/          (daily transaction data)
    - memory/yearly/         (yearly summaries)
    
    Note:
        Uses Path.mkdir with parents=True to create nested directories.
        Silently succeeds if directories already exist (exist_ok=True).
    """
    for directory in [MEMORY_DIR, MONTHLY_DIR, WEEKLY_DIR, DAILY_DIR, YEARLY_DIR]:
        Path(directory).mkdir(parents=True, exist_ok=True)


def save_period_data(period_type: str, period_label: str, metrics: Dict) -> bool:
    """
    Save financial metrics for a specific time period.
    
    Args:
        period_type: 'day', 'week', 'month', or 'year'
        period_label: Label for the period (e.g., '2026-01', '2026-W05')
        metrics: Financial metrics dictionary
        
    Returns:
        True if successful
    """
    ensure_memory_dirs()
    
    # Determine directory
    dir_map = {
        'day': DAILY_DIR,
        'week': WEEKLY_DIR,
        'month': MONTHLY_DIR,
        'year': YEARLY_DIR
    }
    
    target_dir = dir_map.get(period_type)
    if not target_dir:
        logger.error(f"Invalid period type: {period_type}")
        return False
    
    # Save to file
    file_path = os.path.join(target_dir, f"{period_label}.json")
    
    try:
        # Add metadata
        data = {
            **metrics,
            'period_type': period_type,
            'period_label': period_label,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved {period_type} data for {period_label}")
        return True
    except Exception as e:
        logger.error(f"Failed to save {period_type} data: {str(e)}")
        return False


def load_period_data(period_type: str, period_label: str) -> Optional[Dict]:
    """
    Load financial metrics for a specific time period.
    
    Args:
        period_type: 'day', 'week', 'month', or 'year'
        period_label: Label for the period
        
    Returns:
        Metrics dictionary or None
    """
    dir_map = {
        'day': DAILY_DIR,
        'week': WEEKLY_DIR,
        'month': MONTHLY_DIR,
        'year': YEARLY_DIR
    }
    
    target_dir = dir_map.get(period_type)
    if not target_dir:
        return None
    
    file_path = os.path.join(target_dir, f"{period_label}.json")
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Failed to load {period_type} data: {str(e)}")
        return None


def get_all_periods(period_type: str) -> List[Dict]:
    """
    Get all saved periods of a specific type.
    
    Args:
        period_type: 'day', 'week', 'month', or 'year'
        
    Returns:
        List of period data dictionaries
    """
    dir_map = {
        'day': DAILY_DIR,
        'week': WEEKLY_DIR,
        'month': MONTHLY_DIR,
        'year': YEARLY_DIR
    }
    
    target_dir = dir_map.get(period_type)
    if not target_dir or not os.path.exists(target_dir):
        return []
    
    periods = []
    
    try:
        for filename in sorted(os.listdir(target_dir)):
            if filename.endswith('.json'):
                file_path = os.path.join(target_dir, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    periods.append(data)
        return periods
    except Exception as e:
        logger.error(f"Failed to load {period_type} periods: {str(e)}")
        return []


def auto_save_periods(df, segments_dict: Dict[str, any], period_type: str) -> Dict[str, bool]:
    """
    Automatically save all periods from segmented data.
    
    Args:
        df: Original dataframe
        segments_dict: Dictionary of period segments
        period_type: Type of period
        
    Returns:
        Dictionary of period_label: success_status
    """
    from utils.time_periods import get_period_metrics
    
    results = {}
    
    for period_label, period_df in segments_dict.items():
        metrics = get_period_metrics(period_df, period_label)
        success = save_period_data(period_type, period_label, metrics)
        results[period_label] = success
    
    return results


def get_financial_context(period_type: str = 'month', limit: int = 12) -> str:
    """
    Get financial context for chatbot from saved periods.
    
    Args:
        period_type: Type of period to retrieve
        limit: Maximum number of periods to include
        
    Returns:
        Formatted financial context string
    """
    periods = get_all_periods(period_type)
    
    if not periods:
        return "No historical financial data available."
    
    # Take most recent periods
    recent_periods = periods[-limit:] if len(periods) > limit else periods
    
    context_lines = [f"Historical Financial Data ({period_type}ly):"]
    context_lines.append("")
    
    for period_data in recent_periods:
        period_label = period_data.get('period', 'Unknown')
        revenue = period_data.get('revenue', 0)
        expenses = period_data.get('expenses', 0)
        profit = period_data.get('profit', 0)
        margin = period_data.get('profit_margin', 0)
        receivables = period_data.get('receivables', 0)
        
        context_lines.append(f"{period_label}:")
        context_lines.append(f"  Revenue: ₹{revenue:,.0f}")
        context_lines.append(f"  Expenses: ₹{expenses:,.0f}")
        context_lines.append(f"  Profit: ₹{profit:,.0f} ({margin:.1f}% margin)")
        context_lines.append(f"  Receivables: ₹{receivables:,.0f}")
        context_lines.append("")
    
    return "\n".join(context_lines)


def clear_period_data(period_type: str) -> bool:
    """
    Clear all saved data for a period type.
    
    Args:
        period_type: Type of period to clear
        
    Returns:
        True if successful
    """
    dir_map = {
        'day': DAILY_DIR,
        'week': WEEKLY_DIR,
        'month': MONTHLY_DIR,
        'year': YEARLY_DIR
    }
    
    target_dir = dir_map.get(period_type)
    if not target_dir or not os.path.exists(target_dir):
        return True
    
    try:
        for filename in os.listdir(target_dir):
            file_path = os.path.join(target_dir, filename)
            if os.path.isfile(file_path) and filename.endswith('.json'):
                os.remove(file_path)
        logger.info(f"Cleared all {period_type} data")
        return True
    except Exception as e:
        logger.error(f"Failed to clear {period_type} data: {str(e)}")
        return False
