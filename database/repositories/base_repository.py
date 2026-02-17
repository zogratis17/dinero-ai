"""
Base Repository Pattern for Database Operations.
Provides common CRUD operations for all entities.
"""
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from database.models import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository with common database operations.
    Follows repository pattern for clean data access.
    """
    
    def __init__(self, model: Type[ModelType], session: Session):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session
    
    def create(self, **kwargs) -> ModelType:
        """
        Create a new entity.
        
        Args:
            **kwargs: Entity attributes
            
        Returns:
            Created entity
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()  # Get ID without committing
        return instance
    
    def get_by_id(self, entity_id: UUID) -> Optional[ModelType]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            Entity or None if not found
        """
        return self.session.get(self.model, entity_id)
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """
        Get all entities with optional pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of records to skip
            
        Returns:
            List of entities
        """
        query = select(self.model).offset(offset)
        if limit:
            query = query.limit(limit)
        return list(self.session.execute(query).scalars().all())
    
    def update(self, entity_id: UUID, **kwargs) -> Optional[ModelType]:
        """
        Update entity by ID.
        
        Args:
            entity_id: Entity UUID
            **kwargs: Attributes to update
            
        Returns:
            Updated entity or None if not found
        """
        entity = self.get_by_id(entity_id)
        if entity:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            self.session.flush()
        return entity
    
    def delete(self, entity_id: UUID) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if deleted, False if not found
        """
        entity = self.get_by_id(entity_id)
        if entity:
            self.session.delete(entity)
            self.session.flush()
            return True
        return False
    
    def soft_delete(self, entity_id: UUID) -> bool:
        """
        Soft delete entity (if model supports deleted_at).
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if deleted, False if not found
        """
        if hasattr(self.model, 'deleted_at'):
            from datetime import datetime
            return self.update(entity_id, deleted_at=datetime.utcnow()) is not None
        return False
    
    def filter_by(self, **kwargs) -> List[ModelType]:
        """
        Filter entities by attributes.
        
        Args:
            **kwargs: Filter conditions
            
        Returns:
            List of matching entities
        """
        query = select(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        return list(self.session.execute(query).scalars().all())
    
    def count(self, **kwargs) -> int:
        """
        Count entities matching filters.
        
        Args:
            **kwargs: Filter conditions
            
        Returns:
            Count of matching entities
        """
        from sqlalchemy import func
        query = select(func.count()).select_from(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        return self.session.execute(query).scalar() or 0
    
    def exists(self, entity_id: UUID) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if exists
        """
        return self.get_by_id(entity_id) is not None
