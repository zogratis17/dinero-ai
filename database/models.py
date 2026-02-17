"""
SQLAlchemy ORM Models for Dinero AI
Production-grade models with proper relationships and constraints
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
import enum

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Date, DateTime,
    Numeric, Enum as SQLEnum, ForeignKey, CheckConstraint,
    UniqueConstraint, Index, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid


Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class AccountType(str, enum.Enum):
    """Account types for Chart of Accounts"""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"


class GSTType(str, enum.Enum):
    """GST types for Indian taxation"""
    CGST = "cgst"  # Central GST
    SGST = "sgst"  # State GST
    IGST = "igst"  # Integrated GST
    UTGST = "utgst"  # Union Territory GST


class EntrySourceType(str, enum.Enum):
    """Source of journal entry"""
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    AI_SUGGESTED = "ai_suggested"
    SYSTEM_GENERATED = "system_generated"


class MandateStatus(str, enum.Enum):
    """Status of client payment mandate"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AuditAction(str, enum.Enum):
    """Types of audit actions"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"


# ============================================================================
# CORE MODELS
# ============================================================================

class Business(Base):
    """Multi-tenant business entity"""
    __tablename__ = "businesses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_name = Column(String(255), nullable=False)
    gstin = Column(String(15), unique=True, nullable=True)  # Indian GSTIN
    pan = Column(String(10), nullable=True)
    registered_address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    financial_year_start = Column(Integer, default=4)  # April for India
    currency_code = Column(String(3), default='INR')
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    clients = relationship("Client", back_populates="business", cascade="all, delete-orphan")
    chart_of_accounts = relationship("ChartOfAccount", back_populates="business", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="business", cascade="all, delete-orphan")
    financial_snapshots = relationship("FinancialSnapshot", back_populates="business", cascade="all, delete-orphan")
    ai_insights = relationship("AIInsight", back_populates="business", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("gstin IS NULL OR LENGTH(gstin) = 15", name="valid_gstin"),
        CheckConstraint("pan IS NULL OR LENGTH(pan) = 10", name="valid_pan"),
        Index("idx_businesses_active", "is_active"),
        Index("idx_businesses_gstin", "gstin"),
    )


class Client(Base):
    """Customers and vendors"""
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    client_name = Column(String(255), nullable=False)
    client_type = Column(String(50), default="customer")  # customer, vendor, both
    gstin = Column(String(15), nullable=True)
    pan = Column(String(10), nullable=True)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    credit_limit = Column(Numeric(14, 2), default=Decimal("0.00"))
    credit_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    business = relationship("Business", back_populates="clients")
    mandates = relationship("ClientMandate", back_populates="client", cascade="all, delete-orphan")
    journal_entry_lines = relationship("JournalEntryLine", back_populates="client")
    
    __table_args__ = (
        CheckConstraint("credit_limit >= 0", name="valid_credit_limit"),
        CheckConstraint("credit_days >= 0", name="valid_credit_days"),
        Index("idx_clients_business", "business_id"),
        Index("idx_clients_active", "business_id", "is_active"),
        Index("idx_clients_gstin", "gstin"),
        Index("idx_clients_name", "business_id", "client_name"),
    )


class ClientMandate(Base):
    """Payment mandates with encrypted sensitive data"""
    __tablename__ = "client_mandates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    mandate_reference = Column(String(100), nullable=False)
    encrypted_details = Column(JSONB, nullable=False)  # NEVER store raw bank details
    mandate_status = Column(SQLEnum(MandateStatus), default=MandateStatus.ACTIVE)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    max_amount = Column(Numeric(14, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="mandates")
    
    __table_args__ = (
        UniqueConstraint("client_id", "mandate_reference", name="unique_mandate_per_client"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="valid_date_range"),
        Index("idx_mandates_client", "client_id"),
        Index("idx_mandates_status", "client_id", "mandate_status"),
    )


class ChartOfAccount(Base):
    """Chart of accounts for double-entry bookkeeping"""
    __tablename__ = "chart_of_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    account_code = Column(String(50), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=True)
    description = Column(Text, nullable=True)
    gst_applicable = Column(Boolean, default=False)
    is_system_account = Column(Boolean, default=False)  # Cannot be deleted
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="chart_of_accounts")
    parent = relationship("ChartOfAccount", remote_side=[id], backref="children")
    journal_entry_lines = relationship("JournalEntryLine", back_populates="account")
    
    __table_args__ = (
        UniqueConstraint("business_id", "account_code", name="unique_account_code"),
        CheckConstraint("id != parent_id", name="no_self_reference"),
        Index("idx_coa_business", "business_id"),
        Index("idx_coa_type", "business_id", "account_type"),
        Index("idx_coa_parent", "parent_id"),
        Index("idx_coa_active", "business_id", "is_active"),
    )


class JournalEntry(Base):
    """IMMUTABLE journal entry header"""
    __tablename__ = "journal_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    reference_number = Column(String(100), nullable=False)
    entry_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(SQLEnum(EntrySourceType), default=EntrySourceType.MANUAL)
    is_posted = Column(Boolean, default=False)  # Only posted entries are final
    posted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    posted_by = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="journal_entries")
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("business_id", "reference_number", name="unique_reference_number"),
        Index("idx_je_business", "business_id"),
        Index("idx_je_date", "business_id", "entry_date"),
        Index("idx_je_posted", "business_id", "is_posted"),
        Index("idx_je_source", "source_type"),
    )


class JournalEntryLine(Base):
    """IMMUTABLE transaction lines - double-entry"""
    __tablename__ = "journal_entry_lines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True)
    line_number = Column(Integer, nullable=False)
    debit_amount = Column(Numeric(14, 2), default=Decimal("0.00"))
    credit_amount = Column(Numeric(14, 2), default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    gst_category = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartOfAccount", back_populates="journal_entry_lines")
    client = relationship("Client", back_populates="journal_entry_lines")
    gst_records = relationship("GSTRecord", back_populates="journal_entry_line", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "(debit_amount = 0 AND credit_amount > 0) OR (credit_amount = 0 AND debit_amount > 0) OR (debit_amount = 0 AND credit_amount = 0)",
            name="check_debit_or_credit"
        ),
        CheckConstraint("debit_amount >= 0 AND credit_amount >= 0", name="check_non_negative"),
        UniqueConstraint("journal_entry_id", "line_number", name="unique_line_number"),
        Index("idx_jel_entry", "journal_entry_id"),
        Index("idx_jel_account", "account_id"),
        Index("idx_jel_client", "client_id"),
        Index("idx_jel_amounts", "debit_amount", "credit_amount"),
        Index("idx_jel_account_date", "account_id", "journal_entry_id"),
    )


class GSTRecord(Base):
    """GST tax records for Indian compliance"""
    __tablename__ = "gst_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_line_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry_lines.id", ondelete="CASCADE"), nullable=False)
    gst_type = Column(SQLEnum(GSTType), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)  # e.g., 18.00
    gst_amount = Column(Numeric(14, 2), nullable=False)
    hsn_sac_code = Column(String(10), nullable=True)
    itc_eligible = Column(Boolean, default=False)  # Input Tax Credit
    place_of_supply = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    journal_entry_line = relationship("JournalEntryLine", back_populates="gst_records")
    
    __table_args__ = (
        CheckConstraint("gst_rate >= 0 AND gst_rate <= 100", name="valid_gst_rate"),
        CheckConstraint("gst_amount >= 0", name="valid_gst_amount"),
        Index("idx_gst_line", "journal_entry_line_id"),
        Index("idx_gst_type", "gst_type"),
        Index("idx_gst_itc", "itc_eligible"),
    )


# ============================================================================
# AI & ANALYTICS MODELS
# ============================================================================

class FinancialSnapshot(Base):
    """Derived monthly financial snapshots for AI & trends"""
    __tablename__ = "financial_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    month_label = Column(String(20), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    revenue = Column(Numeric(14, 2), default=Decimal("0.00"))
    expenses = Column(Numeric(14, 2), default=Decimal("0.00"))
    profit = Column(Numeric(14, 2), default=Decimal("0.00"))
    receivables = Column(Numeric(14, 2), default=Decimal("0.00"))
    payables = Column(Numeric(14, 2), default=Decimal("0.00"))
    profit_margin = Column(Numeric(5, 2), default=Decimal("0.00"))
    health_score = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="financial_snapshots")
    
    __table_args__ = (
        UniqueConstraint("business_id", "month_label", name="unique_month_snapshot"),
        CheckConstraint("health_score >= 0 AND health_score <= 100", name="valid_health_score"),
        Index("idx_snapshots_business", "business_id"),
        Index("idx_snapshots_date", "business_id", "snapshot_date"),
    )


class AIInsight(Base):
    """AI-generated advisory insights (NOT source of truth)"""
    __tablename__ = "ai_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    month_label = Column(String(20), nullable=True)
    analysis_type = Column(String(50), default="financial_health")
    analysis_summary = Column(Text, nullable=False)
    risk_score = Column(Integer, default=0)
    confidence_score = Column(Numeric(5, 2), default=Decimal("0.00"))
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="ai_insights")
    
    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="valid_risk_score"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 100", name="valid_confidence"),
        Index("idx_insights_business", "business_id"),
        Index("idx_insights_month", "business_id", "month_label"),
        Index("idx_insights_type", "analysis_type"),
    )


# ============================================================================
# AUDIT & SECURITY
# ============================================================================

class AuditLog(Base):
    """Complete audit trail for all changes"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(100), nullable=False)  # Table name
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action_type = Column(SQLEnum(AuditAction), nullable=False)
    old_data = Column(JSONB, nullable=True)
    new_data = Column(JSONB, nullable=True)
    performed_by = Column(String(255), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_audit_business", "business_id"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user", "performed_by"),
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_all_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all tables (use with caution)"""
    Base.metadata.drop_all(engine)
