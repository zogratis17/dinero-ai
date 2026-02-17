"""
Financial Snapshot Repository.
Handles storage and retrieval of monthly financial snapshots.
This bridges the existing JSON memory system with the database.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from database.models import FinancialSnapshot
from database.repositories.base_repository import BaseRepository


class FinancialSnapshotRepository(BaseRepository[FinancialSnapshot]):
    """Repository for financial snapshots"""
    
    def __init__(self, session: Session):
        super().__init__(FinancialSnapshot, session)
    
    def get_by_month(self, business_id: UUID, month_label: str) -> Optional[FinancialSnapshot]:
        """
        Get snapshot for specific month.
        
        Args:
            business_id: Business UUID
            month_label: Month label (e.g., "Jan-2026")
            
        Returns:
            Financial snapshot or None
        """
        query = select(FinancialSnapshot).where(
            FinancialSnapshot.business_id == business_id,
            FinancialSnapshot.month_label == month_label
        )
        return self.session.execute(query).scalar_one_or_none()
    
    def get_recent_history(
        self, 
        business_id: UUID, 
        months: int = 3
    ) -> List[FinancialSnapshot]:
        """
        Get most recent N months of snapshots.
        
        Args:
            business_id: Business UUID
            months: Number of recent months
            
        Returns:
            List of snapshots ordered by date
        """
        query = (
            select(FinancialSnapshot)
            .where(FinancialSnapshot.business_id == business_id)
            .order_by(desc(FinancialSnapshot.snapshot_date))
            .limit(months)
        )
        results = self.session.execute(query).scalars().all()
        return list(reversed(results))  # Return oldest to newest
    
    def save_snapshot(
        self,
        business_id: UUID,
        month_label: str,
        revenue: Decimal,
        expenses: Decimal,
        profit: Decimal,
        receivables: Decimal,
        profit_margin: Decimal,
        health_score: int,
        snapshot_date: Optional[date] = None
    ) -> FinancialSnapshot:
        """
        Save or update financial snapshot.
        
        Args:
            business_id: Business UUID
            month_label: Month identifier
            revenue: Total revenue
            expenses: Total expenses
            profit: Net profit
            receivables: Outstanding receivables
            profit_margin: Profit margin percentage
            health_score: Financial health score (0-100)
            snapshot_date: Date of snapshot (defaults to today)
            
        Returns:
            Saved snapshot
        """
        # Check if snapshot exists
        existing = self.get_by_month(business_id, month_label)
        
        if existing:
            # Update existing
            existing.revenue = revenue
            existing.expenses = expenses
            existing.profit = profit
            existing.receivables = receivables
            existing.profit_margin = profit_margin
            existing.health_score = health_score
            existing.snapshot_date = snapshot_date or date.today()
            self.session.flush()
            return existing
        else:
            # Create new
            return self.create(
                business_id=business_id,
                month_label=month_label,
                snapshot_date=snapshot_date or date.today(),
                revenue=revenue,
                expenses=expenses,
                profit=profit,
                receivables=receivables,
                profit_margin=profit_margin,
                health_score=health_score
            )
    
    def get_all_for_business(self, business_id: UUID) -> List[FinancialSnapshot]:
        """
        Get all snapshots for a business.
        
        Args:
            business_id: Business UUID
            
        Returns:
            List of all snapshots
        """
        query = (
            select(FinancialSnapshot)
            .where(FinancialSnapshot.business_id == business_id)
            .order_by(FinancialSnapshot.snapshot_date)
        )
        return list(self.session.execute(query).scalars().all())
    
    def to_dict(self, snapshot: FinancialSnapshot) -> dict:
        """
        Convert snapshot to dictionary (compatible with JSON memory format).
        
        Args:
            snapshot: Financial snapshot
            
        Returns:
            Dictionary representation
        """
        return {
            "month": snapshot.month_label,
            "revenue": float(snapshot.revenue),
            "expenses": float(snapshot.expenses),
            "profit": float(snapshot.profit),
            "receivables": float(snapshot.receivables),
            "profit_margin": float(snapshot.profit_margin),
            "health_score": snapshot.health_score,
            "timestamp": snapshot.created_at.isoformat()
        }
