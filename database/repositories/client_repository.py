"""
Client Repository.
Handles customer and vendor operations.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from database.models import Client
from database.repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository[Client]):
    """Repository for client entities"""
    
    def __init__(self, session: Session):
        super().__init__(Client, session)
    
    def get_by_business(self, business_id: UUID, active_only: bool = True) -> List[Client]:
        """
        Get all clients for a business.
        
        Args:
            business_id: Business UUID
            active_only: Only return active clients
            
        Returns:
            List of clients
        """
        query = select(Client).where(Client.business_id == business_id)
        if active_only:
            query = query.where(Client.is_active == True, Client.deleted_at == None)
        return list(self.session.execute(query).scalars().all())
    
    def search_by_name(
        self, 
        business_id: UUID, 
        search_term: str
    ) -> List[Client]:
        """
        Search clients by name.
        
        Args:
            business_id: Business UUID
            search_term: Search string
            
        Returns:
            List of matching clients
        """
        query = select(Client).where(
            Client.business_id == business_id,
            Client.client_name.ilike(f"%{search_term}%"),
            Client.deleted_at == None
        )
        return list(self.session.execute(query).scalars().all())
    
    def get_or_create(
        self,
        business_id: UUID,
        client_name: str,
        **kwargs
    ) -> tuple[Client, bool]:
        """
        Get existing client or create new one.
        
        Args:
            business_id: Business UUID
            client_name: Client name
            **kwargs: Additional client attributes
            
        Returns:
            Tuple of (client, created) where created is bool
        """
        # Try to find existing
        query = select(Client).where(
            Client.business_id == business_id,
            Client.client_name == client_name,
            Client.deleted_at == None
        )
        existing = self.session.execute(query).scalar_one_or_none()
        
        if existing:
            return existing, False
        
        # Create new
        client = self.create(
            business_id=business_id,
            client_name=client_name,
            **kwargs
        )
        return client, True
