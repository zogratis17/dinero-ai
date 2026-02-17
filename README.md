# Dinero AI - AI Finance Agent for Indian SMBs

<div align="center">

**An intelligent AI-powered accounting agent that monitors, decides, and acts on your business finances.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Live Demo](#deployment) • [Features](#features) • [Architecture](#architecture) • [Setup](#setup)

</div>

---

## 📋 Problem Statement

Small and Medium Businesses (SMBs) in India face significant challenges in financial management:

- **Manual bookkeeping** is error-prone and time-consuming
- **Delayed insights** lead to missed opportunities and undetected risks
- **GST compliance** is complex with multiple ITC categories
- **Cash flow management** often lacks proactive monitoring
- **No historical analysis** - most tools analyze data in isolation

**Dinero AI** solves these problems by acting as an **autonomous AI accountant** that continuously monitors financial health, detects risks early, and takes proactive actions.

---

## ✨ Features

### 🤖 AI Agent (Reason → Decide → Act)

- Autonomous financial analysis using Google Gemini
- Pattern detection across multiple months
- Proactive risk identification and recommendations
- Auto-generated payment reminder emails

### 🧾 India-Specific GST Classification Engine

- Automatic expense categorization into GST ITC categories
- Identifies claimable vs blocked credits
- Flags items requiring manual review
- Visual breakdown of GST credit distribution

### 📈 Multi-Month Trend Memory (RAG-Lite)

- Persistent financial history storage
- Month-over-month trend visualization
- AI agent uses historical context for analysis
- Detects growth/decline patterns over time

### 🛡️ Enterprise-Grade Features

- Robust error handling with graceful fallbacks
- Input validation and data sanitization
- API retry logic with exponential backoff
- Comprehensive logging

---

## 🏗️ Architecture

```
dinero-ai/
├── app.py                    # Main Streamlit application
├── config/
│   ├── __init__.py
│   └── settings.py           # Centralized configuration
├── services/
│   ├── __init__.py
│   ├── ai_agent.py           # AI Agent with guardrails
│   ├── financial_engine.py   # Financial calculations
│   └── gst_classifier.py     # GST categorization
├── utils/
│   ├── __init__.py
│   ├── memory.py             # Persistent storage
│   └── validators.py         # Input validation
├── tests/
│   └── test_services.py      # Unit tests
├── memory/                   # Financial history (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

### Data Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CSV       │────►│  Validators  │────►│  Financial      │
│   Upload    │     │  (Sanitize)  │     │  Engine         │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Memory    │◄────│  GST         │◄────│  Calculated     │
│   Storage   │     │  Classifier  │     │  Metrics        │
└──────┬──────┘     └──────────────┘     └─────────────────┘
       │                                           │
       ▼                                           ▼
┌─────────────────────────────────────────────────────────┐
│                      AI AGENT                           │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐ │
│  │ Observe │──►│ Reason  │──►│ Decide  │──►│  Act    │ │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Streamlit Dashboard   │
              │   - Insights            │
              │   - Alerts              │
              │   - Email Drafts        │
              └─────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component       | Technology                    |
| --------------- | ----------------------------- |
| Frontend        | Streamlit                     |
| AI/LLM          | Google Gemini 2.5 Flash       |
| Data Processing | Pandas, NumPy                 |
| Visualization   | Plotly                        |
| Memory          | JSON file-based (lightweight) |
| Language        | Python 3.9+                   |

---

## 🚀 Setup

### Prerequisites

- Python 3.9 or higher
- Google Gemini API key

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/zogratis17/dinero-ai.git
   cd dinero-ai
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

---

## 🔐 Responsible AI Usage

Dinero AI implements several guardrails for safe and responsible AI:

### 1. Input Validation

- All CSV inputs are validated for structure and data types
- Text inputs are sanitized to prevent injection attacks
- Amount values are validated as numeric and non-negative

### 2. Output Sanitization

- AI responses are stripped of potentially harmful content
- Script tags and JavaScript are removed
- Response length and quality are validated

### 3. Hallucination Prevention

- AI agent is grounded with real financial data (RAG-lite approach)
- Historical context provides multi-month baseline
- Rule-based actions complement AI recommendations

### 4. Error Handling

- API calls implement retry logic with exponential backoff
- Graceful fallbacks when AI is unavailable
- Comprehensive logging for debugging

### 5. Scope Boundaries

- Agent provides operational advice only
- Tax filing recommendations deferred to CA consultation
- Clear uncertainty flagging in responses

---

## 🗄️ Database Integration (PostgreSQL)

Dinero AI now supports **dual-mode storage**:

- **JSON Mode** (Default): Lightweight file-based storage for quick start
- **PostgreSQL Mode**: Production-grade database with double-entry accounting

### 🚀 Quick Start with Database

1. **Install PostgreSQL** (if not already installed)

   ```bash
   # Windows
   choco install postgresql

   # Mac
   brew install postgresql

   # Linux
   sudo apt-get install postgresql
   ```

2. **Create Database**

   ```bash
   # Connect to PostgreSQL
   psql -U postgres

   # Create database and user
   CREATE DATABASE dinero_ai;
   CREATE USER dinero_user WITH PASSWORD 'dinero_pass';
   GRANT ALL PRIVILEGES ON DATABASE dinero_ai TO dinero_user;
   ```

3. **Configure Environment**

   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env and set:
   USE_DATABASE=true
   DATABASE_URL=postgresql://dinero_user:dinero_pass@localhost:5432/dinero_ai
   ```

4. **Initialize Database**

   ```bash
   # Option 1: Using SQLAlchemy models
   python database/init_db.py --mode sqlalchemy

   # Option 2: Using raw SQL schema
   python database/init_db.py --mode raw_sql
   ```

5. **Run Migrations (Optional)**

   ```bash
   # Generate migration
   alembic revision --autogenerate -m "Initial schema"

   # Apply migrations
   alembic upgrade head
   ```

### 📊 Database Schema Highlights

**Double-Entry Accounting:**

- Full `journal_entries` and `journal_entry_lines` tables
- Automatic debit/credit validation via triggers
- Immutable ledger (no updates/deletes after posting)

**Indian GST Support:**

- `gst_records` table linked to transactions
- CGST, SGST, IGST tracking
- ITC eligibility flags

**Multi-Tenant Ready:**

- `businesses` table for multiple SMBs
- Row-level security enabled
- Business context in all queries

**AI Integration:**

- `financial_snapshots` for monthly metrics
- `ai_insights` for AI recommendations
- Separated from accounting ledger (advisory only)

**Audit Trail:**

- Complete `audit_logs` table
- Tracks all changes with old/new state
- IP address and user tracking

### 🔄 Migration from JSON to Database

The system supports **dual-write mode** for safe migration:

```python
# In app.py or your code
from utils.storage import save_memory, load_memory

# Works in both JSON and DB mode automatically!
entry = {
    "month": "Jan-2026",
    "revenue": 100000,
    "expenses": 50000,
    "profit": 50000,
    "receivables": 20000,
    "profit_margin": 50.0
}

# Automatically routes to JSON or DB based on USE_DATABASE flag
save_memory(entry, business_id=your_business_uuid)

# Load history (from JSON or DB)
history = load_memory()
```

### 📚 Database API Examples

```python
from database.connection import db_session
from database.repositories import (
    BusinessRepository,
    ClientRepository,
    FinancialSnapshotRepository
)

# Create business with default chart of accounts
with db_session() as session:
    biz_repo = BusinessRepository(session)
    business = biz_repo.create_with_default_accounts(
        business_name="My Startup",
        gstin="29ABCDE1234F1Z5",
        pan="ABCDE1234F"
    )

# Add client
with db_session() as session:
    client_repo = ClientRepository(session)
    client, created = client_repo.get_or_create(
        business_id=business.id,
        client_name="ABC Corp",
        email="contact@abccorp.com"
    )

# Save financial snapshot
with db_session() as session:
    snapshot_repo = FinancialSnapshotRepository(session)
    snapshot_repo.save_snapshot(
        business_id=business.id,
        month_label="Feb-2026",
        revenue=Decimal("150000"),
        expenses=Decimal("75000"),
        profit=Decimal("75000"),
        receivables=Decimal("30000"),
        profit_margin=Decimal("50.0"),
        health_score=85
    )
```

### 🔒 Security Features

- **UUID Primary Keys**: Prevents ID enumeration attacks
- **Row-Level Security**: Multi-tenant data isolation
- **Encrypted Mandates**: Sensitive payment data encrypted in JSONB
- **NUMERIC for Money**: Prevents floating-point errors
- **Foreign Key Constraints**: Data integrity enforcement
- **Audit Logging**: Complete change trail

### ⚙️ Configuration Options

```bash
# .env file
USE_DATABASE=true                    # Enable DB mode
DATABASE_URL=postgresql://...        # Connection string
DB_POOL_SIZE=5                       # Connection pool size
DB_MAX_OVERFLOW=10                   # Max extra connections
DB_POOL_TIMEOUT=30                   # Connection timeout (seconds)
DB_ECHO=false                        # Log SQL queries (debug)
```

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=services --cov=utils --cov=database
```

---

## 🌐 Deployment

### Streamlit Cloud (JSON Mode)

1. Push code to GitHub
2. Connect repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in Streamlit dashboard:
   ```toml
   GEMINI_API_KEY = "your_api_key"
   USE_DATABASE = "false"
   ```
4. Deploy!

### Docker with PostgreSQL

```bash
# Use docker-compose for full stack
docker-compose up -d

# Or build manually
docker build -t dinero-ai .
docker run -p 8501:8501 \
  -e USE_DATABASE=true \
  -e DATABASE_URL=postgresql://user:pass@host:5432/dinero_ai \
  dinero-ai
```

### Production Deployment (with Database)

**Prerequisites:**

- PostgreSQL 14+ database
- Environment variables configured

**Steps:**

1. **Setup Database**

   ```bash
   # Run on production server
   psql -U postgres < database/schema.sql
   ```

2. **Configure Environment**

   ```bash
   export USE_DATABASE=true
   export DATABASE_URL=postgresql://user:pass@prod-db:5432/dinero_ai
   export GEMINI_API_KEY=your_key
   ```

3. **Run Migrations**

   ```bash
   alembic upgrade head
   ```

4. **Start Application**
   ```bash
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   ```

**Cloud Database Options:**

- AWS RDS (PostgreSQL)
- Google Cloud SQL
- Azure Database for PostgreSQL
- Supabase
- Neon

---

## 📊 Sample Data Format

```csv
date,client,description,amount,type,status
2026-01-01,ABC Corp,Website Project,50000,income,paid
2026-01-10,XYZ Ltd,Consulting,30000,income,unpaid
2026-01-12,AWS,AWS Cloud Subscription,12000,expense,paid
2026-01-15,Landlord,Office Rent,20000,expense,paid
```

---

## 🎯 Roadmap

### ✅ Completed

- [x] PostgreSQL database integration
- [x] Double-entry accounting schema
- [x] Multi-tenant architecture
- [x] GST compliance tracking
- [x] Audit logging system
- [x] Repository pattern data access

### 🚧 In Progress / Future

- [ ] Double-entry UI for manual journal entries
- [ ] CSV to journal entry mapping
- [ ] Chart of accounts management UI
- [ ] Ollama AI backend integration
- [ ] Cash runway prediction
- [ ] Prophet-style forecasting
- [ ] PDF report export
- [ ] Multi-currency support
- [ ] Invoice generation
- [ ] Bank statement import
- [ ] Multi-business dashboard
- [ ] Role-based access control

---

## 👥 Team

Built for AgentX Hackathon 2026

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
