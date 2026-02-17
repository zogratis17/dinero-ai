"""
Time-based data segmentation and analysis utilities.
Provides functions to segment financial data by day, week, month, year.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def segment_by_period(df: pd.DataFrame, period: str = 'month') -> Dict[str, pd.DataFrame]:
    """
    Segment ledger data by time period.
    
    Args:
        df: DataFrame with 'date' column (will be converted to datetime)
        period: Time period for segmentation. Options:
            - 'day': Segment by individual days
            - 'week': Segment by weeks
            - 'month': Segment by months (default)
            - 'year': Segment by years
        
    Returns:
        Dictionary mapping period labels to DataFrames.
        Period labels format:
            - day: 'YYYY-MM-DD' (e.g., '2026-02-15')
            - week: 'YYYY-WNN' (e.g., '2026-W07')
            - month: 'YYYY-MM' (e.g., '2026-02')
            - year: 'YYYY' (e.g., '2026')
        
    Raises:
        ValueError: If invalid period type is provided
        
    Example:
        >>> monthly_data = segment_by_period(df, 'month')
        >>> for month, month_df in monthly_data.items():
        ...     print(f"{month}: {len(month_df)} transactions")
    """
    if df.empty or 'date' not in df.columns:
        return {}
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    segments = {}
    
    if period == 'day':
        df['period_key'] = df['date'].dt.strftime('%Y-%m-%d')
        group_col = 'period_key'
    elif period == 'week':
        df['period_key'] = df['date'].dt.strftime('%Y-W%U')  # Year-Week
        group_col = 'period_key'
    elif period == 'month':
        df['period_key'] = df['date'].dt.strftime('%Y-%m')  # Year-Month
        group_col = 'period_key'
    elif period == 'year':
        df['period_key'] = df['date'].dt.strftime('%Y')  # Year
        group_col = 'period_key'
    else:
        raise ValueError(f"Invalid period: {period}. Use 'day', 'week', 'month', or 'year'")
    
    # Group by period
    for period_label, group_df in df.groupby(group_col):
        segments[period_label] = group_df.drop(columns=['period_key'])
    
    return segments


def get_period_metrics(df: pd.DataFrame, period_label: str) -> Dict:
    """
    Calculate financial metrics for a specific time period.
    
    Args:
        df: DataFrame for the period
        period_label: Label for the period
        
    Returns:
        Dictionary of metrics
    """
    from services.financial_engine import calculate_financials
    
    metrics = calculate_financials(df)
    metrics['period'] = period_label
    metrics['transaction_count'] = len(df)
    
    return metrics


def compare_periods(current: Dict, previous: Dict) -> Dict:
    """
    Compare two periods and calculate changes.
    
    Args:
        current: Current period metrics
        previous: Previous period metrics
        
    Returns:
        Dictionary with comparison statistics
    """
    comparison = {}
    
    metrics_to_compare = ['revenue', 'expenses', 'profit', 'receivables', 'profit_margin']
    
    for metric in metrics_to_compare:
        current_val = current.get(metric, 0)
        previous_val = previous.get(metric, 0)
        
        # Calculate absolute change
        change = current_val - previous_val
        
        # Calculate percentage change
        if previous_val != 0:
            pct_change = (change / previous_val) * 100
        else:
            pct_change = 100 if current_val > 0 else 0
        
        comparison[f'{metric}_change'] = change
        comparison[f'{metric}_pct_change'] = pct_change
    
    return comparison


def get_available_periods(df: pd.DataFrame, period_type: str = 'month') -> List[str]:
    """
    Get list of available periods in the data.
    
    Args:
        df: DataFrame with date column
        period_type: 'day', 'week', 'month', or 'year'
        
    Returns:
        Sorted list of period labels
    """
    if df.empty or 'date' not in df.columns:
        return []
    
    df['date'] = pd.to_datetime(df['date'])
    
    if period_type == 'day':
        periods = df['date'].dt.strftime('%Y-%m-%d').unique()
    elif period_type == 'week':
        periods = df['date'].dt.strftime('%Y-W%U').unique()
    elif period_type == 'month':
        periods = df['date'].dt.strftime('%Y-%m').unique()
    elif period_type == 'year':
        periods = df['date'].dt.strftime('%Y').unique()
    else:
        return []
    
    return sorted(periods.tolist())


def format_period_label(period_key: str, period_type: str) -> str:
    """
    Format period key into user-friendly label.
    
    Args:
        period_key: Period identifier (e.g., '2026-01', '2026-W05')
        period_type: Type of period
        
    Returns:
        Formatted label
    """
    if period_type == 'day':
        try:
            date_obj = datetime.strptime(period_key, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')  # January 15, 2026
        except:
            return period_key
    elif period_type == 'week':
        return f"Week {period_key.split('-W')[1]}, {period_key.split('-')[0]}"
    elif period_type == 'month':
        try:
            date_obj = datetime.strptime(period_key + '-01', '%Y-%m-%d')
            return date_obj.strftime('%B %Y')  # January 2026
        except:
            return period_key
    elif period_type == 'year':
        return period_key
    else:
        return period_key


def get_trend_direction(comparison: Dict, metric: str) -> str:
    """
    Determine trend direction for a metric.
    
    Args:
        comparison: Comparison dictionary
        metric: Metric name
        
    Returns:
        'up', 'down', or 'stable'
    """
    pct_change = comparison.get(f'{metric}_pct_change', 0)
    
    if abs(pct_change) < 5:  # Less than 5% change
        return 'stable'
    elif pct_change > 0:
        return 'up'
    else:
        return 'down'
