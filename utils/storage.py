"""
Storage Abstraction Layer.
Provides unified interface for both JSON and Database storage.
Allows seamless migration from JSON to PostgreSQL.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from uuid import UUID

from config.settings import USE_DATABASE

# Import both storage backends
from utils.memory import (
    load_memory as json_load_memory,
    save_memory as json_save_memory,
    get_recent_history as json_get_recent_history,
    format_history_for_agent as json_format_history
)

# Database imports (conditional)
if USE_DATABASE:
    from database.connection import db_session
    from database.repositories.snapshot_repository import FinancialSnapshotRepository
    from decimal import Decimal

logger = logging.getLogger(__name__)


class FinancialDataService:
    """
    Unified interface for financial data storage.
    Routes to JSON or Database based on configuration.
    """
    
    @staticmethod
    def save_snapshot(entry: Dict[str, Any], business_id: Optional[UUID] = None) -> bool:
        """
        Save financial snapshot to storage.
        
        Args:
            entry: Financial snapshot data
            business_id: Business UUID (required for DB mode)
            
        Returns:
            True if saved successfully
        """
        if USE_DATABASE:
            return FinancialDataService._save_to_database(entry, business_id)
        else:
            return FinancialDataService._save_to_json(entry)
    
    @staticmethod
    def load_history() -> List[Dict[str, Any]]:
        """
        Load all financial history.
        
        Returns:
            List of financial snapshots
        """
        if USE_DATABASE:
            return FinancialDataService._load_from_database()
        else:
            return json_load_memory()
    
    @staticmethod
    def get_recent_history(months: int = 3, business_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Get recent N months of history.
        
        Args:
            months: Number of months
            business_id: Business UUID (required for DB mode)
            
        Returns:
            List of recent snapshots
        """
        if USE_DATABASE:
            return FinancialDataService._get_recent_from_database(months, business_id)
        else:
            return json_get_recent_history(months)
    
    @staticmethod
    def format_for_agent(history: List[Dict[str, Any]]) -> str:
        """
        Format history for AI agent.
        
        Args:
            history: List of snapshots
            
        Returns:
            Formatted string
        """
        if USE_DATABASE:
            import json
            return json.dumps(history, indent=2, default=str)
        else:
            return json_format_history(history)
    
    # ========================================================================
    # Private Methods - JSON Backend
    # ========================================================================
    
    @staticmethod
    def _save_to_json(entry: Dict[str, Any]) -> bool:
        """Save to JSON file"""
        try:
            return json_save_memory(entry)
        except Exception as e:
            logger.error(f"JSON save failed: {str(e)}")
            return False
    
    # ========================================================================
    # Private Methods - Database Backend
    # ========================================================================
    
    @staticmethod
    def _save_to_database(entry: Dict[str, Any], business_id: Optional[UUID] = None) -> bool:
        """Save to PostgreSQL database"""
        if not business_id:
            logger.error("business_id required for database mode")
            return False
        
        try:
            with db_session() as session:
                repo = FinancialSnapshotRepository(session)
                
                repo.save_snapshot(
                    business_id=business_id,
                    month_label=entry.get("month", ""),
                    revenue=Decimal(str(entry.get("revenue", 0))),
                    expenses=Decimal(str(entry.get("expenses", 0))),
                    profit=Decimal(str(entry.get("profit", 0))),
                    receivables=Decimal(str(entry.get("receivables", 0))),
                    profit_margin=Decimal(str(entry.get("profit_margin", 0))),
                    health_score=int(entry.get("health_score", 0))
                )
                
            logger.info(f"Saved snapshot to database: {entry.get('month')}")
            return True
            
        except Exception as e:
            logger.error(f"Database save failed: {str(e)}")
            return False
    
    @staticmethod
    def _load_from_database(business_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Load all snapshots from database"""
        try:
            with db_session() as session:
                repo = FinancialSnapshotRepository(session)
                
                if business_id:
                    snapshots = repo.get_all_for_business(business_id)
                else:
                    # If no business_id, get from first business (demo mode)
                    from database.repositories.business_repository import BusinessRepository
                    biz_repo = BusinessRepository(session)
                    businesses = biz_repo.get_active_businesses()
                    if not businesses:
                        return []
                    snapshots = repo.get_all_for_business(businesses[0].id)
                
                return [repo.to_dict(s) for s in snapshots]
                
        except Exception as e:
            logger.error(f"Database load failed: {str(e)}")
            return []
    
    @staticmethod
    def _get_recent_from_database(months: int, business_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get recent history from database"""
        try:
            with db_session() as session:
                repo = FinancialSnapshotRepository(session)
                
                if business_id:
                    snapshots = repo.get_recent_history(business_id, months)
                else:
                    # Demo mode - use first business
                    from database.repositories.business_repository import BusinessRepository
                    biz_repo = BusinessRepository(session)
                    businesses = biz_repo.get_active_businesses()
                    if not businesses:
                        return []
                    snapshots = repo.get_recent_history(businesses[0].id, months)
                
                return [repo.to_dict(s) for s in snapshots]
                
        except Exception as e:
            logger.error(f"Database recent history failed: {str(e)}")
            return []


# ============================================================================
# Convenience Functions (Drop-in replacements)
# ============================================================================

def save_memory(entry: Dict[str, Any], business_id: Optional[UUID] = None) -> bool:
    """Save financial snapshot (auto-routes to JSON or DB)"""
    return FinancialDataService.save_snapshot(entry, business_id)


def load_memory() -> List[Dict[str, Any]]:
    """Load all history (auto-routes to JSON or DB)"""
    return FinancialDataService.load_history()


def get_recent_history(months: int = 3, business_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
    """Get recent history (auto-routes to JSON or DB)"""
    return FinancialDataService.get_recent_history(months, business_id)


def format_history_for_agent(history: List[Dict[str, Any]]) -> str:
    """Format history for AI agent"""
    return FinancialDataService.format_for_agent(history)
