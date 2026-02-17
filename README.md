# Dinero AI - AI Finance Agent for Indian SMBs

<div align="center">

**An intelligent AI-powered accounting agent that monitors, decides, and acts on your business finances.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

🌐 **[Live Demo](https://dinero-ai.streamlit.app/)** | [Features](#-features) • [Architecture](#%EF%B8%8F-architecture) • [Setup](#-setup) • [Database](#%EF%B8%8F-database-integration-postgresql)

</div>

---

## 📋 Problem Statement

Small and Medium Businesses (SMBs) in India face significant challenges in financial management:

- **Manual bookkeeping** is error-prone and time-consuming
- **Delayed insights** lead to missed opportunities and undetected risks
- **GST compliance** is complex with multiple ITC categories (eligible, blocked, review-required)
- **Cash flow management** often lacks proactive monitoring and forecasting
- **No historical analysis** - most tools analyze data in isolation without trends
- **Limited AI integration** - existing solutions lack conversational AI and autonomous decision-making

**Dinero AI** solves these problems by acting as an **autonomous AI accountant** that continuously monitors financial health, detects risks early, provides conversational assistance, and enables proactive financial management.

---

## ✨ Features

### 🤖 AI Agent (Reason → Decide → Act)

- **Autonomous financial analysis** using Google Gemini 2.5 Flash with configurable Ollama support
- **Modular AI insights** with independent analysis sections:
  - Executive Summary
  - Financial Diagnosis
  - Trend Analysis (multi-period comparison)
  - Cash Flow Risk Assessment
  - GST Analysis & Optimization
  - Actionable Recommendations
  - Urgent Actions Identification
- **Pattern detection** across multiple time periods (daily, weekly, monthly, yearly)
- **Proactive risk identification** with severity classification (critical/warning)
- **Auto-generated payment reminder emails** for overdue clients
- **Responsible AI guardrails**: hallucination prevention, output sanitization, scope boundaries

### 💬 Conversational AI Chatbot

- **Context-aware financial assistant** with access to full historical data
- **Natural language queries** about revenue, expenses, trends, clients, and GST
- **Multi-turn conversations** with session memory
- **Prompt injection protection** with keyword-based guardrails
- **Financial domain enforcement** - rejects non-finance queries
- **Historical context integration** - answers reference up to 12 months of data

### 🧾 India-Specific GST Classification Engine

- **Automated expense categorization** into GST ITC categories:
  - ITC Eligible (Capital Goods, Input Services, Business Expenses)
  - Blocked Credits (Rent, Food, Fuel, Entertainment, CSR)
  - Review Required (Mixed Use, Partial ITC, Ambiguous Cases)
- **Rule-based classification** with keyword matching and amount thresholds
- **GST summary dashboard** with claimable vs non-claimable breakdown
- **Visual analytics** for GST credit distribution

### 📈 Enhanced Multi-Period Trend Memory (RAG-Lite)

- **Automatic time-based segmentation**: Daily, Weekly, Monthly, Yearly
- **Persistent financial history** with JSON-based storage system
- **Multi-period trend visualization** with interactive Plotly charts
- **Period-over-period comparison** with percentage change calculations
- **AI agent historical context** - uses past 3-12 months for pattern detection
- **Growth/decline pattern analysis** with visual indicators

### 📄 PDF Report Generation

- **Monthly financial statement PDFs** with professional formatting
- **Comprehensive metrics**: Revenue, Expenses, Profit, Margins, Receivables
- **GST breakdown** included in reports
- **Trend charts** embedded in PDF
- **Downloadable from UI** for any historical month

### 🗄️ Database Integration (Dual Mode)

- **JSON Mode** (default): Lightweight file-based storage for quick start
- **PostgreSQL Mode**: Production-grade database with:
  - **Double-entry accounting** with journal entries and ledger
  - **Multi-tenant architecture** with business isolation
  - **Audit logging** for complete change tracking
  - **Row-level security** for data protection
  - **SQLAlchemy ORM** with repository pattern
  - **Alembic migrations** for schema versioning
  - **Immutable ledger** with posting constraints

### 📧 Gmail Integration

- **OAuth 2.0 authentication** for secure email access
- **Send payment reminders** directly from the app
- **Email draft generation** via AI agent

### 🛡️ Enterprise-Grade Features

- **Comprehensive error handling** with graceful fallbacks
- **Input validation & sanitization** (CSV structure, data types, SQL injection prevention)
- **API retry logic** with exponential backoff
- **Structured logging** with configurable levels
- **Secure credential management** with `.env` files
- **Modular architecture** with separation of concerns
- **Unit tests** for core services and utilities

---

## 🏗️ Architecture

### Project Structure

```
dinero-ai/
├── app.py                           # Main Streamlit application (765 lines)
├── config/
│   ├── __init__.py
│   └── settings.py                  # Centralized configuration & constants
├── services/
│   ├── __init__.py
│   ├── ai_agent.py                  # AI Agent with guardrails & modular analysis
│   ├── chatbot.py                   # Conversational AI with security
│   ├── financial_engine.py          # Financial calculations & health scoring
│   ├── gmail_service.py             # Gmail API integration
│   └── gst_classifier.py            # GST categorization engine
├── utils/
│   ├── __init__.py
│   ├── enhanced_memory.py           # Multi-period storage (day/week/month/year)
│   ├── memory.py                    # Legacy memory system
│   ├── pdf_generator.py             # PDF report creation
│   ├── storage.py                   # Dual-mode storage (JSON/PostgreSQL)
│   ├── time_periods.py              # Time segmentation utilities
│   └── validators.py                # Input validation & sanitization
├── database/
│   ├── __init__.py
│   ├── connection.py                # Database connection & session management
│   ├── init_db.py                   # Database initialization script
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── schema.sql                   # Raw SQL schema
│   └── repositories/
│       ├── __init__.py
│       ├── base_repository.py       # Base repository pattern
│       ├── business_repository.py   # Business entity operations
│       ├── client_repository.py     # Client management
│       └── snapshot_repository.py   # Financial snapshot storage
├── tests/
│   ├── __init__.py
│   ├── test_chatbot.py              # Chatbot tests
│   ├── test_enhanced_memory.py      # Memory system tests
│   ├── test_services.py             # Service layer tests
│   └── test_time_periods.py         # Time period tests
├── knowledge/
│   └── gst_rules.txt                # GST knowledge base for AI
├── memory/                          # Auto-generated (gitignored)
│   ├── financial_history.json
│   ├── daily/
│   ├── weekly/
│   ├── monthly/
│   └── yearly/
├── alembic/                         # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── .streamlit/                      # Streamlit config
├── requirements.txt                 # Python dependencies
├── docker-compose.yml               # Docker orchestration
├── Dockerfile                       # Container definition
├── alembic.ini                      # Alembic configuration
├── .env.example                     # Environment template
└── README.md
```

### Data Flow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CSV       │────►│  Validators  │────►│  Financial      │
│   Upload    │     │  (Sanitize)  │     │  Engine         │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                    ┌──────────────────────────────┤
                    │                              │
                    ▼                              ▼
         ┌─────────────────┐          ┌─────────────────────┐
         │  Time Period    │          │  GST                │
         │  Segmentation   │          │  Classifier         │
         │  (D/W/M/Y)     │          └──────────┬──────────┘
         └────────┬────────┘                     │
                  │                              │
                  ▼                              ▼
         ┌─────────────────┐          ┌─────────────────────┐
         │  Enhanced       │◄─────────│  Calculated         │
         │  Memory         │          │  Metrics +          │
         │  (JSON/DB)      │          │  GST Summary        │
         └────────┬────────┘          └─────────────────────┘
                  │
                  ▼
         ┌─────────────────────────────────────────────┐
         │           STREAMLIT UI (6 TABS)             │
         ├─────────────────────────────────────────────┤
         │  1. Dashboard      - Health metrics & KPIs  │
         │  2. AI Chatbot     - Conversational Q&A     │
         │  3. AI Analysis    - Modular insights       │
         │  4. GST Analysis   - ITC breakdown          │
         │  5. Trends         - Multi-period charts    │
         │  6. Ledger         - Filtered transactions  │
         └──────────────────┬──────────────────────────┘
                            │
         ┌──────────────────┴────────────────────┐
         │                                       │
         ▼                                       ▼
┌─────────────────┐                    ┌─────────────────┐
│  AI AGENT       │                    │  PDF Generator  │
│  (Gemini/Ollama)│                    │  (ReportLab)    │
│                 │                    └─────────────────┘
│  - Context      │
│  - RAG-Lite     │
│  - Guardrails   │
└─────────────────┘
```
---

## 🛠️ Tech Stack

| Component            | Technology                           |
| -------------------- | ------------------------------------ |
| **Frontend**         | Streamlit 1.28+                      |
| **AI/LLM**           | Google Gemini 2.5 Flash (configurable Ollama) |
| **Database**         | PostgreSQL 15+ (optional)            |
| **ORM**              | SQLAlchemy 2.0                       |
| **Migrations**       | Alembic                              |
| **Data Processing**  | Pandas, NumPy                        |
| **Visualization**    | Plotly, Matplotlib                   |
| **PDF Generation**   | ReportLab, Pillow, Kaleido           |
| **Email**            | Gmail API (OAuth 2.0)                |
| **Storage**          | JSON (default) / PostgreSQL          |
| **Testing**          | pytest, pytest-cov                   |
| **Containerization** | Docker, Docker Compose               |
| **Language**         | Python 3.9+                          |

---

## 🚀 Setup

### Prerequisites

- **Python 3.9 or higher**
- **Google Gemini API key** (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- **PostgreSQL 15+** (optional, for database mode)
- **Gmail OAuth credentials** (optional, for email features)

### Quick Start (JSON Mode)

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
   # Copy example file
   cp .env.example .env

   # Edit .env and set:
   # GEMINI_API_KEY=your_api_key_here
   # USE_DATABASE=false
   ```

5. **Run the application**

   ```bash
   streamlit run app.py
   ```

6. **Access the app** at [http://localhost:8501](http://localhost:8501)

### Gmail Integration Setup (Optional)

To enable email reminder features:

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API

2. **Create OAuth 2.0 Credentials**
   - Navigate to APIs & Services → Credentials
   - Create OAuth 2.0 Client ID (Desktop application)
   - Download credentials as `credentials.json`
   - Place in project root directory

3. **First-time authentication**
   - Run the app and try to send an email
   - Browser will open for Google OAuth flow
   - Grant permissions
   - `token.json` will be auto-generated

---

## 🔐 Responsible AI Practices

Dinero AI implements comprehensive guardrails for safe, reliable, and responsible AI usage:

### 1. Input Validation & Sanitization

- **CSV structure validation** - verifies required columns (date, client, description, amount, type, status)
- **Data type validation** - ensures amounts are numeric and non-negative
- **SQL injection prevention** - parameterized queries in database mode
- **Text input sanitization** - removes dangerous characters and scripts
- **Date format validation** - enforces consistent date parsing

### 2. Output Sanitization & Safety

- **Script injection removal** - strips `<script>` tags and JavaScript
- **HTML sanitization** - removes potentially harmful HTML content
- **Response length validation** - ensures minimum quality thresholds
- **Content filtering** - blocks inappropriate or harmful outputs

### 3. AI Hallucination Prevention

- **Grounded analysis** - AI agent receives real financial data (RAG-lite approach)
- **Historical context** - uses 3-12 months of saved data as baseline
- **Rule-based validation** - financial calculations verified independently
- **Response validation** - checks for common hallucination patterns
- **Fallback mechanisms** - system continues operating if AI is unavailable

### 4. Prompt Injection Protection (Chatbot)

- **Keyword-based guardrails** - rejects non-finance queries
- **Blocked pattern detection** - identifies prompt injection attempts:
  - "ignore previous instructions"
  - "forget everything"
  - "act as"
  - "you are now"
  - System prompt manipulation
- **Finance domain enforcement** - requires finance-related keywords
- **System prompt isolation** - protects core agent behavior

### 5. Error Resilience

- **API retry logic** - exponential backoff for Gemini API (max 3 retries)
- **Graceful degradation** - app functions without AI in limited mode
- **Comprehensive error handling** - try/except blocks with specific exceptions
- **Structured logging** - detailed logs for debugging and monitoring
- **User-friendly error messages** - actionable feedback on failures

### 6. Scope Boundaries & Disclaimers

- **Operational advice only** - focuses on business operations, not legal/tax filing
- **CA consultation recommendations** - defers tax filing to qualified professionals
- **Uncertainty flagging** - AI clearly states when it's uncertain
- **No financial guarantees** - explicitly states advisory nature
- **Limited scope prompts** - system prompts constrain AI behavior

### 7. Data Privacy & Security

- **Local data storage** - financial data stored locally by default
- **Gitignored sensitive files** - `.env`, `token.json`, `credentials.json`, `memory/`
- **No data transmission** - JSON mode doesn't send data externally (except to Gemini for analysis)
- **OAuth 2.0 for Gmail** - secure authentication without password storage
- **Environment-based secrets** - API keys stored in `.env` files

### 8. Audit & Observability

- **Comprehensive logging** - all major operations logged
- **Database audit trail** - complete change history in PostgreSQL mode
- **User action tracking** - monitors what users do in the app
- **Error tracking** - failed operations logged for debugging

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

The project includes comprehensive test coverage for core functionality.

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=services --cov=utils --cov=database --cov-report=html

# Run specific test file
pytest tests/test_chatbot.py -v
pytest tests/test_enhanced_memory.py -v
pytest tests/test_time_periods.py -v
```

### Test Coverage

- **`test_chatbot.py`** - Chatbot security, prompt injection, finance domain validation
- **`test_enhanced_memory.py`** - Multi-period storage, period comparison, data persistence
- **`test_services.py`** - Financial calculations, GST classification, health scoring
- **`test_time_periods.py`** - Time segmentation, period formatting, date handling

### Continuous Integration

Tests can be integrated with GitHub Actions, GitLab CI, or other CI/CD pipelines:

```yaml
# Example: .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov --cov-report=xml
```

---

## 📊 Sample Data Format

### CSV Structure

The application accepts ledger data in CSV format with the following required columns:

```csv
date,client,description,amount,type,status
2026-01-01,ABC Corp,Website Project,50000,income,paid
2026-01-10,XYZ Ltd,Consulting,30000,income,unpaid
2026-01-12,AWS,AWS Cloud Subscription,12000,expense,paid
2026-01-15,Landlord,Office Rent,20000,expense,paid
2026-01-20,Google,Google Workspace,500,expense,paid
2026-01-25,Client ABC,Software Development,75000,income,paid
```

### Column Specifications

| Column      | Type   | Description                                  | Valid Values                |
| ----------- | ------ | -------------------------------------------- | --------------------------- |
| `date`      | Date   | Transaction date (YYYY-MM-DD or DD/MM/YYYY)  | Any valid date format       |
| `client`    | String | Client/vendor name                           | Any text                    |
| `description` | String | Transaction description                    | Any text                    |
| `amount`    | Number | Transaction amount (positive numbers)        | Any positive number         |
| `type`      | String | Transaction type                             | `income` or `expense`       |
| `status`    | String | Payment status                               | `paid` or `unpaid`          |

### Sample Data

A sample ledger file is included: `sample_ledger.csv`

### Data Validation

The app automatically validates:
- ✅ Required columns presence
- ✅ Data types (amount must be numeric)
- ✅ Non-negative amounts
- ✅ Valid transaction types
- ✅ Date format consistency

Invalid data will show clear error messages with actionable fixes.

---

## 💡 Usage Guide

### 1. Upload Ledger

- Click "📤 Upload Ledger CSV"
- Select your CSV file
- Data is automatically validated and processed

### 2. Dashboard Tab

- View **Financial Health Score** (0-100)
- Monitor **KPIs**: Revenue, Expenses, Profit, Outstanding
- See **Risk Alerts** with recommendations
- Check **Income vs Expenses** pie chart

### 3. AI Chatbot Tab

- Ask questions in natural language:
  - "What was my revenue last month?"
  - "Which client owes the most money?"
  - "How is my profit margin trending?"
  - "What GST credits can I claim?"
- Bot has context of all historical data (up to 12 months)
- Conversation history maintained during session

### 4. AI Analysis Tab

- Click individual buttons for specific analysis:
  - **Executive Summary**: High-level overview
  - **Financial Diagnosis**: Detailed health assessment
  - **Trend Analysis**: Historical comparisons
  - **Cash Flow Risks**: Liquidity warnings
  - **GST Analysis**: ITC optimization
  - **Recommendations**: Actionable advice
  - **Urgent Actions**: Priority items
- Or click **"Run All"** for comprehensive analysis
- Each section generated independently for faster response

### 5. GST Analysis Tab

- View automatic GST categorization:
  - **ITC Eligible**: Claimable input tax credit
  - **Blocked Credits**: Non-claimable (rent, food, fuel, etc.)
  - **Review Required**: Ambiguous cases needing manual review
- Visual bar chart of GST distribution
- Detailed expense breakdown table

### 6. Trends & History Tab

- Switch between **Day**, **Week**, **Month**, **Year** views
- Interactive time-series charts:
  - Revenue vs Expenses trend
  - Profit over time
  - Outstanding receivables
  - Profit margin percentage
- **Period Comparison**: Compare any two periods side-by-side
- **Download PDF**: Generate monthly financial statement (monthly view only)

### 7. Ledger Data Tab

- **Filter transactions** by type, status, month
- View **filtered summary metrics**
- **Download filtered data** as CSV
- Full transaction table with search/sort

---

## 🎯 Roadmap

### ✅ Completed Features (v1.0)

- [x] **Core Application**
  - [x] Streamlit UI with 6-tab navigation
  - [x] CSV ledger upload and validation
  - [x] Financial metrics calculation
  - [x] Health scoring system
  - [x] Risk detection and alerts

- [x] **AI & Intelligence**
  - [x] Google Gemini integration with guardrails
  - [x] Modular AI analysis (7 independent sections)
  - [x] Conversational AI chatbot with context
  - [x] Prompt injection protection
  - [x] RAG-lite with historical memory

- [x] **GST Compliance**
  - [x] Automatic expense categorization
  - [x] ITC eligibility detection
  - [x] Blocked credit identification
  - [x] GST summary dashboard
  - [x] Visual analytics

- [x] **Time-Based Analytics**
  - [x] Multi-period segmentation (daily, weekly, monthly, yearly)
  - [x] Enhanced memory system with persistent storage
  - [x] Trend visualization (Plotly charts)
  - [x] Period-over-period comparison
  - [x] Historical context for AI (3-12 months)

- [x] **Database & Storage**
  - [x] Dual-mode storage (JSON/PostgreSQL)
  - [x] PostgreSQL schema with double-entry accounting
  - [x] SQLAlchemy ORM with repository pattern
  - [x] Alembic migrations
  - [x] Multi-tenant architecture
  - [x] Audit logging system
  - [x] Database initialization scripts

- [x] **Reporting**
  - [x] PDF monthly financial statements
  - [x] Professional report formatting (ReportLab)
  - [x] Embedded charts in PDF
  - [x] CSV export for filtered data

- [x] **Integrations**
  - [x] Gmail API OAuth 2.0
  - [x] Email reminder generation
  - [x] Payment reminder drafts

- [x] **Developer Experience**
  - [x] Comprehensive test suite (pytest)
  - [x] Docker support
  - [x] Docker Compose orchestration
  - [x] Environment configuration (.env)
  - [x] Extensive documentation
  - [x] Sample data included

### 🚧 In Progress / Planned (v2.0)

- [ ] **Enhanced AI Features**
  - [ ] Ollama local LLM support (configuration ready)
  - [ ] Cash runway prediction with Prophet forecasting
  - [ ] Anomaly detection (unusual expenses/income)
  - [ ] Automated insight prioritization
  - [ ] Multi-language support (Hindi, regional languages)

- [ ] **Database Enhancements**
  - [ ] CSV to double-entry journal mapping UI
  - [ ] Manual journal entry creation in UI
  - [ ] Chart of accounts management UI
  - [ ] Account reconciliation features
  - [ ] Automated bank statement import
  - [ ] Duplicate transaction detection

- [ ] **GST Enhancements**
  - [ ] GSTR-1/GSTR-3B draft generation
  - [ ] HSN/SAC code integration
  - [ ] E-invoice format support
  - [ ] GST reconciliation with GSTN portal
  - [ ] Reverse charge mechanism detection

- [ ] **Advanced Analytics**
  - [ ] Interactive dashboards with drill-down
  - [ ] Custom date range selection
  - [ ] Cohort analysis for client retention
  - [ ] Expense category trends
  - [ ] Budget vs actual comparison
  - [ ] Variance analysis

- [ ] **Collaboration & Multi-User**
  - [ ] Multi-business dashboard (switch between businesses)
  - [ ] Role-based access control (RBAC)
  - [ ] User management & permissions
  - [ ] Shared access for accountants/CAs
  - [ ] Activity audit trail per user

- [ ] **Automation**
  - [ ] Recurring transaction templates
  - [ ] Automated email reminders (scheduled)
  - [ ] Webhook support for integrations
  - [ ] Zapier/Make.com integration
  - [ ] Slack/Discord notifications

- [ ] **Compliance & Reporting**
  - [ ] TDS calculation and tracking
  - [ ] Professional tax computation
  - [ ] Annual report generation
  - [ ] P&L statement (detailed)
  - [ ] Balance sheet
  - [ ] Cash flow statement

- [ ] **Mobile & Accessibility**
  - [ ] Mobile-responsive UI improvements
  - [ ] Progressive Web App (PWA) support
  - [ ] iOS/Android companion app
  - [ ] Accessibility compliance (WCAG)

### 🎨 Future Vision (v3.0+)

- [ ] **AI Agents**
  - [ ] Autonomous weekly financial reviews
  - [ ] Proactive anomaly alerts via email/SMS
  - [ ] Smart vendor negotiation suggestions
  - [ ] Automated expense approval workflows

- [ ] **Advanced Integrations**
  - [ ] Zoho Books / Tally integration
  - [ ] Payment gateway integration (Razorpay, Stripe)
  - [ ] Banking API (Plaid equivalent for India)
  - [ ] E-commerce platform sync (Shopify, WooCommerce)

- [ ] **ML & Forecasting**
  - [ ] Revenue forecasting (Prophet/ARIMA)
  - [ ] Expense prediction
  - [ ] Churn risk scoring for clients
  - [ ] Optimal payment timing recommendations

- [ ] **Enterprise Features**
  - [ ] SSO (SAML/OAuth) support
  - [ ] On-premise deployment option
  - [ ] API for third-party integrations
  - [ ] White-label customization
  - [ ] SLA-backed support tiers

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

1. **Report Bugs** - Open an issue with detailed reproduction steps
2. **Suggest Features** - Share your ideas in GitHub Discussions
3. **Improve Documentation** - Fix typos, add examples, clarify instructions
4. **Submit Code** - Fix bugs or implement features via Pull Requests

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/zogratis17/dinero-ai.git
cd dinero-ai

# Create a feature branch
git checkout -b feature/your-feature-name

# Setup development environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Make your changes
# ...

# Run tests again
pytest tests/ -v --cov

# Commit and push
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### Code Standards

- **Formatting**: Follow PEP 8 style guide
- **Documentation**: Add docstrings to all functions/classes
- **Type Hints**: Use type hints where applicable
- **Testing**: Include tests for new features
- **Logging**: Use structured logging for debugging

### Pull Request Process

1. Update README.md with any new features/changes
2. Ensure all tests pass
3. Update relevant documentation
4. Link related issues in PR description
5. Wait for maintainer review

---

## ❓ FAQ

### General Questions

**Q: What is Dinero AI?**  
A: Dinero AI is an autonomous AI-powered accounting agent for Indian SMBs that monitors financial health, provides insights, and helps with GST compliance.

**Q: Is it free to use?**  
A: Yes, the software is open-source (MIT License). You only need a free Google Gemini API key for AI features.

**Q: Do I need accounting knowledge to use it?**  
A: No! The AI explains everything in simple terms. However, for complex tax matters, consult a CA.

### Technical Questions

**Q: What data format do I need?**  
A: Upload a CSV with columns: `date, client, description, amount, type, status`. See sample format in app.

**Q: Can I use it without a database?**  
A: Yes! JSON mode works out of the box. PostgreSQL is optional for production use.

**Q: Is my financial data safe?**  
A: In JSON mode, all data stays on your machine. Only analysis text is sent to Gemini (not raw transactions). In database mode, ensure you secure your database.

**Q: Can I use Ollama instead of Gemini?**  
A: Configuration is ready in `.env`, but integration is not yet complete. Coming in v2.0.

**Q: How do I backup my data?**  
A: **JSON mode**: Copy the `memory/` folder. **Database mode**: Run `pg_dump` on PostgreSQL.

### Business Questions

**Q: Can accountants/CAs use this?**  
A: Absolutely! It's designed to assist professionals and business owners alike.

**Q: Does it support GST filing?**  
A: It helps with ITC categorization and analysis, but doesn't file returns. Use GSTN portal for filing.

**Q: Can multiple users access the same business data?**  
A: Multi-user support is planned for v2.0. Currently, it's single-user per deployment.

**Q: What about TDS, professional tax, etc.?**  
A: TDS and other compliance features are in the roadmap for v2.0.

---

## 📝 Changelog

### v1.0.0 (February 2026) - Initial Release

#### Features
- ✨ 6-tab Streamlit UI (Dashboard, Chatbot, AI Analysis, GST, Trends, Ledger)
- 🤖 Modular AI analysis with 7 independent sections
- 💬 Conversational AI chatbot with financial context
- 🧾 Automatic GST classification (ITC eligible, blocked, review)
- 📈 Multi-period analytics (daily, weekly, monthly, yearly)
- 📄 PDF monthly report generation
- 🗄️ Dual storage mode (JSON/PostgreSQL)
- 🐘 Full PostgreSQL schema with double-entry accounting
- 📧 Gmail integration for payment reminders
- 🔐 Comprehensive AI guardrails and security
- 🐳 Docker and Docker Compose support
- ✅ Test suite with pytest

#### Infrastructure
- Repository pattern for data access
- Alembic database migrations
- Environment-based configuration
- Structured logging
- Error handling and retry logic

---

## 👥 Team

**Team La Espada - Built for AgentX Hackathon 2026**

### Team Members

- **Hari Prasath N T** ([@zogratis17](https://github.com/zogratis17)) - Lead Developer
- **Vijesh** ([@vijesh-5](https://github.com/vijesh-5)) - Collaborator
- **Madhu Shankara G S** ([@madhushankara](https://github.com/madhushankara)) - Collaborator
- **Velayuthyam V** ([@velayutham-07](https://github.com/velayutham-07)) - Collaborator

### Contributors

See all contributors at [Contributors Graph](https://github.com/zogratis17/dinero-ai/graphs/contributors)

### Acknowledgments

- **Google Gemini** - AI/LLM capabilities
- **Streamlit** - Rapid UI development
- **PostgreSQL** - Robust database foundation
- **Open Source Community** - Various libraries and tools

---

## 📄 License

MIT License

Copyright (c) 2026 Dinero AI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 📞 Support & Contact

### Get Help

- 📖 **Documentation**: Read this README and inline code comments
- 🐛 **Bug Reports**: [Open an issue](https://github.com/zogratis17/dinero-ai/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/zogratis17/dinero-ai/discussions)
- 📧 **Contact**: Via GitHub Issues or Discussions

### Community

- ⭐ **Star this repo** if you find it useful!
- 🔀 **Fork & customize** for your needs
- 🐦 **Share** on social media
- 💬 **Discuss** features and improvements

---

## 🙏 Acknowledgments & Credits

### Technologies

- **[Streamlit](https://streamlit.io/)** - Amazing framework for data apps
- **[Google Gemini](https://ai.google.dev/)** - Powerful AI capabilities
- **[PostgreSQL](https://www.postgresql.org/)** - World's most advanced open-source database
- **[Plotly](https://plotly.com/)** - Beautiful interactive charts
- **[ReportLab](https://www.reportlab.com/)** - PDF generation
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Python SQL toolkit

### Inspiration

This project was built to address real challenges faced by Indian SMBs in financial management, inspired by:
- The complexity of GST compliance
- Lack of affordable AI-powered accounting tools
- Need for proactive financial monitoring
- Desire to democratize financial intelligence

---

<div align="center">

**Made with ❤️ for Indian SMBs**

[⭐ Star on GitHub](https://github.com/zogratis17/dinero-ai) • [🐛 Report Bug](https://github.com/zogratis17/dinero-ai/issues) • [💡 Request Feature](https://github.com/zogratis17/dinero-ai/discussions)

</div>
