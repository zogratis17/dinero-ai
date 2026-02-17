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

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| AI/LLM | Google Gemini 2.5 Flash |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly |
| Memory | JSON file-based (lightweight) |
| Language | Python 3.9+ |

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

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=services --cov=utils
```

---

## 🌐 Deployment

### Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Connect repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add `GEMINI_API_KEY` in Streamlit secrets
4. Deploy!

### Docker (Alternative)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

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

## 🎯 Future Roadmap

- [ ] Cash runway prediction
- [ ] Prophet-style forecasting
- [ ] PDF report export
- [ ] Multi-currency support
- [ ] Invoice generation
- [ ] Bank statement import

---

## 👥 Team

Built for AgentX Hackathon 2026

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
