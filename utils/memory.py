"""
Memory Management - Persistent storage for financial history.
Implements RAG-style financial memory across sessions.
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.settings import MEMORY_DIR, MEMORY_FILE

logger = logging.getLogger(__name__)


def ensure_memory_dir() -> bool:
    """
    Ensure the memory directory exists.
    
    Returns:
        True if directory exists or was created successfully, False otherwise
        
    Note:
        Creates the directory with proper permissions if it doesn't exist.
        Logs any errors that occur during creation.
    """
    try:
        if not os.path.exists(MEMORY_DIR):
            os.makedirs(MEMORY_DIR)
            logger.info(f"Created memory directory: {MEMORY_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create memory directory: {str(e)}")
        return False


def load_memory() -> List[Dict[str, Any]]:
    """
    Load financial history from persistent storage.
    
    Returns:
        List of historical financial entries
    """
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Validate data structure
                if isinstance(data, list):
                    return data
                else:
                    logger.warning("Invalid memory format, returning empty list")
                    return []
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse memory file: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Failed to load memory: {str(e)}")
        return []


def save_memory(entry: Dict[str, Any]) -> bool:
    """
    Save a financial entry to persistent storage.
    
    Args:
        entry: Dictionary containing month's financial data.
               Should include 'month' key for identifying the entry.
        
    Returns:
        True if save was successful, False otherwise
        
    Note:
        - Automatically adds timestamp if not present
        - Updates existing entry if month already exists (prevents duplicates)
        - Creates memory directory if it doesn't exist
        
    Example:
        >>> entry = {'month': '2026-02', 'revenue': 100000, 'profit': 25000}
        >>> success = save_memory(entry)
    """
    try:
        # Ensure directory exists
        ensure_memory_dir()
        
        # Load existing history
        history = load_memory()
        
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
        
        # Check for duplicate month entries
        existing_months = [h.get("month") for h in history]
        if entry.get("month") in existing_months:
            # Update existing entry instead of duplicating
            for i, h in enumerate(history):
                if h.get("month") == entry.get("month"):
                    history[i] = entry
                    logger.info(f"Updated existing entry for {entry.get('month')}")
                    break
        else:
            history.append(entry)
            logger.info(f"Added new entry for {entry.get('month')}")
        
        # Save to file
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save memory: {str(e)}")
        return False


def get_recent_history(months: int = 3) -> List[Dict[str, Any]]:
    """
    Get the most recent financial history entries.
    
    Args:
        months: Number of recent months to retrieve
        
    Returns:
        List of recent financial entries
    """
    history = load_memory()
    return history[-months:] if history else []


def format_history_for_agent(history: List[Dict[str, Any]]) -> str:
    """
    Format history data for AI agent context.
    
    Args:
        history: List of historical entries
        
    Returns:
        JSON formatted string for agent prompt
    """
    if not history:
        return "No past data available"
    
    return json.dumps(history, indent=2, ensure_ascii=False)


def clear_memory() -> bool:
    """
    Clear all financial history (use with caution).
    
    Returns:
        True if cleared successfully
    """
    try:
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
            logger.info("Memory cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear memory: {str(e)}")
        return False


def get_memory_stats() -> Dict[str, Any]:
    """
    Get statistics about stored memory.
    
    Returns:
        Dictionary with memory statistics
    """
    history = load_memory()
    
    if not history:
        return {
            "total_months": 0,
            "first_entry": None,
            "last_entry": None,
            "avg_revenue": 0,
            "avg_profit": 0
        }
    
    revenues = [h.get("revenue", 0) for h in history]
    profits = [h.get("profit", 0) for h in history]
    
    return {
        "total_months": len(history),
        "first_entry": history[0].get("month"),
        "last_entry": history[-1].get("month"),
        "avg_revenue": sum(revenues) / len(revenues) if revenues else 0,
        "avg_profit": sum(profits) / len(profits) if profits else 0
    }
