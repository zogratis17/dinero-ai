"""
Business Repository.
Handles business entity operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from database.models import Business
from database.repositories.base_repository import BaseRepository


class BusinessRepository(BaseRepository[Business]):
    """Repository for business entities"""
    
    def __init__(self, session: Session):
        super().__init__(Business, session)
    
    def get_by_gstin(self, gstin: str) -> Optional[Business]:
        """
        Get business by GSTIN.
        
        Args:
            gstin: Indian GSTIN number
            
        Returns:
            Business or None
        """
        query = select(Business).where(Business.gstin == gstin)
        return self.session.execute(query).scalar_one_or_none()
    
    def get_active_businesses(self):
        """Get all active businesses"""
        return self.filter_by(is_active=True)
    
    def create_with_default_accounts(
        self,
        business_name: str,
        **kwargs
    ) -> Business:
        """
        Create business with default chart of accounts.
        
        Args:
            business_name: Name of the business
            **kwargs: Additional business attributes
            
        Returns:
            Created business with chart of accounts
        """
        from sqlalchemy import text
        
        # Create business
        business = self.create(business_name=business_name, **kwargs)
        self.session.flush()
        
        # Create default chart of accounts using stored function
        self.session.execute(
            text("SELECT create_default_chart_of_accounts(:business_id)"),
            {"business_id": business.id}
        )
        
        return business
