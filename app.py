"""
Dinero AI - AI Finance Agent for Indian SMBs

Main Streamlit application entry point.
This is a modular, production-ready application with proper error handling,
input validation, and responsible AI practices.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import logging
import os
from datetime import datetime

# Local imports
from config.settings import PAGE_TITLE, PAGE_LAYOUT, HIGH_RECEIVABLES_THRESHOLD, CLIENT_CONCENTRATION_THRESHOLD
from services.gst_classifier import classify_gst, get_gst_summary
from services.financial_engine import calculate_financials, get_overdue_clients, assess_financial_health, format_financial_state
from services.ai_agent import DineroAgent, AIAgentError
from utils.memory import load_memory, save_memory, get_recent_history, format_history_for_agent, ensure_memory_dir
from utils.validators import validate_ledger, clean_dataframe, sanitize_text_input, validate_month_label

# Database imports
from database.connection import init_db, db_session, DatabaseConnection
from database.models import Business, Client, ChartOfAccount, JournalEntry, JournalEntryLine, AccountType, EntrySourceType
from decimal import Decimal
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)

# Ensure memory directory exists
ensure_memory_dir()

# Initialize database connection
try:
    init_db()
    logger.info("Database connection initialized")
except Exception as e:
    logger.warning(f"Database initialization failed: {str(e)}. Running without database features.")


def create_transaction_signature(row) -> str:
    """Create a unique signature for transaction duplicate detection."""
    # Convert date to string format and handle potential datetime objects
    date_str = str(row['date'])[:10] if pd.notna(row['date']) else ''
    
    # Normalize text fields for better duplicate detection
    client_normalized = str(row['client']).lower().strip().replace(' ', '') if pd.notna(row['client']) else ''
    description_normalized = str(row['description']).lower().strip().replace(' ', '') if pd.notna(row['description']) else ''
    
    # Normalize amount to consistent format (2 decimal places)
    if pd.notna(row['amount']):
        amount_normalized = f"{float(row['amount']):.2f}"
    else:
        amount_normalized = "0.00"
    
    type_normalized = str(row['type']).lower().strip() if pd.notna(row['type']) else ''
    
    # Create signature from key fields
    signature_data = f"{date_str}|{client_normalized}|{description_normalized}|{amount_normalized}|{type_normalized}"
    return hashlib.md5(signature_data.encode()).hexdigest()


def get_or_create_default_accounts(business_id, session):
    """Get or create default chart of accounts for a business."""
    default_accounts = [
        {"code": "1000", "name": "Bank Account", "type": AccountType.ASSET},
        {"code": "4000", "name": "Revenue", "type": AccountType.INCOME},
        {"code": "5000", "name": "Expenses", "type": AccountType.EXPENSE},
        {"code": "1200", "name": "Accounts Receivable", "type": AccountType.ASSET},
    ]
    
    accounts = {}
    for account_data in default_accounts:
        account = session.query(ChartOfAccount).filter_by(
            business_id=business_id,
            account_code=account_data["code"]
        ).first()
        
        if not account:
            account = ChartOfAccount(
                business_id=business_id,
                account_code=account_data["code"],
                account_name=account_data["name"],
                account_type=account_data["type"],
                is_system_account=True,
                is_active=True
            )
            session.add(account)
            session.flush()  # Get the ID
        
        accounts[account_data["name"]] = account
    
    return accounts


def get_or_create_client(client_name: str, business_id, session):
    """Get or create client record."""
    client = session.query(Client).filter_by(
        business_id=business_id,
        client_name=client_name,
        is_active=True
    ).first()
    
    if not client:
        client = Client(
            business_id=business_id,
            client_name=client_name,
            client_type="customer",
            is_active=True
        )
        session.add(client)
        session.flush()
    
    return client


def filter_duplicate_transactions(new_transactions_df, business_id):
    """Filter out duplicate transactions by comparing with existing database records."""
    try:
        with db_session() as session:
            # Create signatures for new transactions
            new_transactions_df['signature'] = new_transactions_df.apply(create_transaction_signature, axis=1)
            
            # Get existing journal entries from the last 6 months to check for duplicates
            six_months_ago = datetime.now().date().replace(day=1)
            for _ in range(6):  # Go back 6 months
                six_months_ago = six_months_ago.replace(day=1)
                if six_months_ago.month == 1:
                    six_months_ago = six_months_ago.replace(year=six_months_ago.year - 1, month=12)
                else:
                    six_months_ago = six_months_ago.replace(month=six_months_ago.month - 1)
            
            existing_entries = session.query(JournalEntry).filter(
                JournalEntry.business_id == business_id,
                JournalEntry.entry_date >= six_months_ago
            ).all()
            
            # Create signatures for existing transactions
            existing_signatures = set()
            for entry in existing_entries:
                # Get client name from the first line with a client
                client_name = ""
                amount = Decimal('0.00')
                transaction_type = "expense"  # default
                
                for line in entry.lines:
                    if line.client:
                        client_name = line.client.client_name
                    if line.debit_amount > 0:
                        amount = line.debit_amount
                        # Bank account debit = income transaction
                        if line.account.account_type == AccountType.ASSET:
                            transaction_type = "income"
                        else:
                            transaction_type = "expense"
                    elif line.credit_amount > 0:
                        amount = line.credit_amount
                        # Revenue account credit = income transaction  
                        if line.account.account_type == AccountType.INCOME:
                            transaction_type = "income"
                        else:
                            transaction_type = "expense"
                
                # Create signature using same normalization logic
                client_normalized = client_name.lower().strip().replace(' ', '') if client_name else ''
                description_normalized = str(entry.description).lower().strip().replace(' ', '') if entry.description else ''
                amount_normalized = f"{float(amount):.2f}"
                type_normalized = transaction_type.lower().strip()
                
                signature_data = f"{str(entry.entry_date)}|{client_normalized}|{description_normalized}|{amount_normalized}|{type_normalized}"
                signature = hashlib.md5(signature_data.encode()).hexdigest()
                existing_signatures.add(signature)
            
            # Filter out duplicates
            new_only = new_transactions_df[~new_transactions_df['signature'].isin(existing_signatures)].copy()
            duplicates = new_transactions_df[new_transactions_df['signature'].isin(existing_signatures)].copy()
            
            return new_only.drop('signature', axis=1), len(duplicates)
    
    except Exception as e:
        logger.error(f"Error filtering duplicates: {str(e)}")
        # Return all transactions if filtering fails
        return new_transactions_df, 0


def save_transactions_to_database(transactions_df, business_id):
    """Save individual transactions to database as journal entries."""
    saved_count = 0
    
    try:
        with db_session() as session:
            # Get or create default accounts
            accounts = get_or_create_default_accounts(business_id, session)
            
            for _, row in transactions_df.iterrows():
                try:
                    # Get or create client
                    client = get_or_create_client(str(row['client']), business_id, session)
                    
                    # Create journal entry with unique reference
                    timestamp_part = datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_id = str(uuid.uuid4())[:8]
                    reference_number = f"CSV-{timestamp_part}-{unique_id}"
                    
                    journal_entry = JournalEntry(
                        business_id=business_id,
                        reference_number=reference_number,
                        entry_date=pd.to_datetime(row['date']).date(),
                        description=str(row['description']),
                        source_type=EntrySourceType.CSV_IMPORT,
                        is_posted=True,
                        posted_at=datetime.now(),
                        created_by="CSV Import"
                    )
                    session.add(journal_entry)
                    session.flush()  # Get the journal entry ID
                    
                    # Create double-entry lines
                    amount = Decimal(str(row['amount']))
                    transaction_type = str(row['type']).lower()
                    
                    if transaction_type == 'income':
                        # Debit: Bank Account, Credit: Revenue
                        # Line 1: Debit Bank
                        line1 = JournalEntryLine(
                            journal_entry_id=journal_entry.id,
                            account_id=accounts["Bank Account"].id,
                            client_id=client.id,
                            line_number=1,
                            debit_amount=amount,
                            credit_amount=Decimal('0.00'),
                            description=str(row['description']),
                            gst_category=str(row.get('gst_category', ''))
                        )
                        
                        # Line 2: Credit Revenue
                        line2 = JournalEntryLine(
                            journal_entry_id=journal_entry.id,
                            account_id=accounts["Revenue"].id,
                            client_id=client.id,
                            line_number=2,
                            debit_amount=Decimal('0.00'),
                            credit_amount=amount,
                            description=str(row['description']),
                            gst_category=str(row.get('gst_category', ''))
                        )
                    
                    else:  # expense
                        # Debit: Expense, Credit: Bank Account
                        # Line 1: Debit Expense
                        line1 = JournalEntryLine(
                            journal_entry_id=journal_entry.id,
                            account_id=accounts["Expenses"].id,
                            client_id=client.id,
                            line_number=1,
                            debit_amount=amount,
                            credit_amount=Decimal('0.00'),
                            description=str(row['description']),
                            gst_category=str(row.get('gst_category', ''))
                        )
                        
                        # Line 2: Credit Bank
                        line2 = JournalEntryLine(
                            journal_entry_id=journal_entry.id,
                            account_id=accounts["Bank Account"].id,
                            client_id=client.id,
                            line_number=2,
                            debit_amount=Decimal('0.00'),
                            credit_amount=amount,
                            description=str(row['description']),
                            gst_category=str(row.get('gst_category', ''))
                        )
                    
                    session.add(line1)
                    session.add(line2)
                    saved_count += 1
                
                except Exception as e:
                    logger.error(f"Error saving transaction: {str(e)}")
                    continue
    
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
    
    return saved_count


def display_database_tab():
    """Display database management and viewing features."""
    st.header("📊 Database & Transaction History")
    
    default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    try:
        with db_session() as session:
            # Database Statistics
            st.subheader("📈 Database Overview")
            
            # Get counts
            business_count = session.query(Business).count()
            client_count = session.query(Client).filter_by(business_id=default_business_id, is_active=True).count()
            account_count = session.query(ChartOfAccount).filter_by(business_id=default_business_id, is_active=True).count()
            entry_count = session.query(JournalEntry).filter_by(business_id=default_business_id).count()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Businesses", business_count)
            col2.metric("Active Clients", client_count)
            col3.metric("Chart of Accounts", account_count)
            col4.metric("Journal Entries", entry_count)
            
            # Recent Transactions
            st.subheader("💳 Recent Transactions")
            
            recent_entries = session.query(JournalEntry) \
                .filter_by(business_id=default_business_id) \
                .order_by(JournalEntry.entry_date.desc()) \
                .limit(20).all()
            
            if recent_entries:
                transactions_data = []
                for entry in recent_entries:
                    client_name = "N/A"
                    amount = 0
                    transaction_type = "Unknown"
                    
                    for line in entry.lines:
                        if line.client:
                            client_name = line.client.client_name
                        if line.debit_amount > 0:
                            amount = float(line.debit_amount)
                            if line.account.account_type == AccountType.ASSET:
                                transaction_type = "Income"
                            else:
                                transaction_type = "Expense"
                        elif line.credit_amount > 0:
                            amount = float(line.credit_amount)
                            if line.account.account_type == AccountType.INCOME:
                                transaction_type = "Income"
                            else:
                                transaction_type = "Expense"
                    
                    transactions_data.append({
                        "Date": entry.entry_date,
                        "Reference": entry.reference_number,
                        "Client": client_name,
                        "Description": entry.description,
                        "Amount": f"₹{amount:,.2f}",
                        "Type": transaction_type,
                        "Status": "Posted" if entry.is_posted else "Draft"
                    })
                
                df_transactions = pd.DataFrame(transactions_data)
                st.dataframe(df_transactions, use_container_width=True)
            else:
                st.info("No transactions found in the database.")
            
            # Chart of Accounts
            st.subheader("📋 Chart of Accounts")
            
            accounts = session.query(ChartOfAccount) \
                .filter_by(business_id=default_business_id, is_active=True) \
                .order_by(ChartOfAccount.account_code).all()
            
            if accounts:
                accounts_data = [{
                    "Code": acc.account_code,
                    "Name": acc.account_name,
                    "Type": acc.account_type.value,
                    "System Account": "Yes" if acc.is_system_account else "No"
                } for acc in accounts]
                
                df_accounts = pd.DataFrame(accounts_data)
                st.dataframe(df_accounts, use_container_width=True)
            else:
                st.info("No chart of accounts found.")
                
                # Offer to create default accounts
                if st.button("🔧 Create Default Chart of Accounts"):
                    accounts = get_or_create_default_accounts(default_business_id, session)
                    session.commit()
                    st.success("✅ Default accounts created! Refresh the page to see them.")
    
    except Exception as e:
        st.error(f"❌ Error accessing database: {str(e)}")
        logger.error(f"Database error: {str(e)}")


def display_clients_tab():
    """Display client management features."""
    st.header("👥 Client Management")
    
    default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    try:
        with db_session() as session:
            # Client Statistics
            st.subheader("📊 Client Overview") 
            
            clients = session.query(Client) \
                .filter_by(business_id=default_business_id, is_active=True) \
                .order_by(Client.client_name).all()
            
            if clients:
                st.metric("Total Active Clients", len(clients))
                
                # Client List
                st.subheader("📋 Client Directory")
                
                clients_data = []
                for client in clients:
                    # Calculate client transaction summary
                    total_transactions = session.query(JournalEntryLine) \
                        .filter_by(client_id=client.id).count()
                    
                    # Get latest transaction date
                    latest_transaction = session.query(JournalEntryLine) \
                        .join(JournalEntry) \
                        .filter(JournalEntryLine.client_id == client.id) \
                        .order_by(JournalEntry.entry_date.desc()) \
                        .first()
                    
                    latest_date = latest_transaction.journal_entry.entry_date if latest_transaction else "Never"
                    
                    clients_data.append({
                        "Name": client.client_name,
                        "Type": client.client_type.title(),
                        "Email": client.email or "Not provided",
                        "Phone": client.phone or "Not provided",
                        "Transactions": total_transactions,
                        "Last Transaction": latest_date,
                        "Credit Limit": f"₹{client.credit_limit:,.2f}",
                        "Credit Days": client.credit_days
                    })
                
                df_clients = pd.DataFrame(clients_data)
                st.dataframe(df_clients, use_container_width=True)
                
                # Client Details Expander
                st.subheader("🔍 Client Details")
                selected_client = st.selectbox("Select a client to view details:", 
                                               options=[client.client_name for client in clients])
                
                if selected_client:
                    client = next((c for c in clients if c.client_name == selected_client), None)
                    if client:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Name:** {client.client_name}")
                            st.write(f"**Type:** {client.client_type.title()}")  
                            st.write(f"**Email:** {client.email or 'Not provided'}")
                            st.write(f"**Phone:** {client.phone or 'Not provided'}")
                            
                        with col2:
                            st.write(f"**Credit Limit:** ₹{client.credit_limit:,.2f}")
                            st.write(f"**Credit Days:** {client.credit_days}")
                            st.write(f"**Created:** {client.created_at.strftime('%Y-%m-%d') if client.created_at else 'Unknown'}")
                            st.write(f"**Status:** {'Active' if client.is_active else 'Inactive'}")
                        
                        # Recent transactions for this client
                        st.write("**Recent Transactions:**")
                        client_transactions = session.query(JournalEntryLine) \
                            .join(JournalEntry) \
                            .filter(JournalEntryLine.client_id == client.id) \
                            .order_by(JournalEntry.entry_date.desc()) \
                            .limit(10).all()
                        
                        if client_transactions:
                            trans_data = [{
                                "Date": line.journal_entry.entry_date,
                                "Description": line.journal_entry.description,
                                "Debit": f"₹{line.debit_amount:,.2f}" if line.debit_amount > 0 else "-",
                                "Credit": f"₹{line.credit_amount:,.2f}" if line.credit_amount > 0 else "-",
                                "Reference": line.journal_entry.reference_number
                            } for line in client_transactions]
                            
                            df_client_trans = pd.DataFrame(trans_data)
                            st.dataframe(df_client_trans, use_container_width=True)
                        else:
                            st.info("No transactions found for this client.")
            else:
                st.info("No clients found in the database.")
                st.write("Clients will be automatically created when you upload CSV files with transaction data.")
    
    except Exception as e:
        st.error(f"❌ Error accessing client data: {str(e)}")
        logger.error(f"Client data error: {str(e)}")


def display_settings_tab():
    """Display application settings and configuration."""  
    st.header("⚙️ Application Settings")
    
    # Database Configuration
    st.subheader("🗄️ Database Configuration")
    
    from config.settings import USE_DATABASE, DATABASE_URL, USE_DATABASE as use_db
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Database Enabled:** {'✅ Yes' if use_db else '❌ No'}")
        if use_db:
            # Test database connection
            try:
                from database.connection import DatabaseConnection
                is_connected = DatabaseConnection.health_check()
                st.write(f"**Database Connection:** {'✅ Connected' if is_connected else '❌ Disconnected'}")
            except Exception as e:
                st.write(f"**Database Connection:** ❌ Error - {str(e)}")
        
        st.write(f"**Database URL:** {DATABASE_URL[:30]}..." if DATABASE_URL else "Not configured")
    
    with col2:
        # Memory Configuration  
        st.write("**Memory Storage:** JSON + Database")
        
        # Check memory directory
        from config.settings import MEMORY_DIR, MEMORY_FILE
        memory_exists = os.path.exists(MEMORY_FILE) 
        st.write(f"**Memory File:** {'✅ Exists' if memory_exists else '❌ Not found'}")
        
        if memory_exists:
            # Show memory stats
            try:
                from utils.memory import load_memory
                history = load_memory()
                st.write(f"**Memory Entries:** {len(history)}")
            except Exception as e:
                st.write(f"**Memory Entries:** ❌ Error loading")
    
    # Memory Management
    st.subheader("💾 Memory Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Memory"):
            try:
                from utils.memory import load_memory
                history = load_memory()
                if history:
                    st.write(f"Found {len(history)} memory entries:")
                    df_memory = pd.DataFrame(history)
                    st.dataframe(df_memory)
                else:
                    st.info("No memory entries found.")
            except Exception as e:
                st.error(f"Error loading memory: {str(e)}")
    
    with col2:
        if st.button("🧹 Clear Memory"):
            st.warning("⚠️ This will permanently delete all saved financial history.")
            confirm_clear = st.checkbox("I understand and want to clear all memory")
            if confirm_clear and st.button("🗑️ Confirm Clear Memory"):
                try:
                    if os.path.exists(MEMORY_FILE):
                        os.remove(MEMORY_FILE)
                        st.success("✅ Memory cleared successfully!")
                        st.rerun()
                    else:
                        st.info("Memory file not found.")
                except Exception as e:
                    st.error(f"Error clearing memory: {str(e)}")
    
    with col3:
        if st.button("🔄 Reset Database"):
            st.warning("⚠️ This would reset the entire database. This feature is not implemented for safety.")
    
    # AI Agent Configuration
    st.subheader("🤖 AI Agent Configuration")
    
    from config.settings import GEMINI_API_KEY, USE_OLLAMA
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_configured = bool(GEMINI_API_KEY)
        st.write(f"**Gemini API Key:** {'✅ Configured' if api_configured else '❌ Not configured'}")
        st.write(f"**Ollama Enabled:** {'✅ Yes' if USE_OLLAMA else '❌ No'}")
    
    with col2:
        # Test AI connectivity
        if st.button("🧪 Test AI Connection"):
            try:
                from services.ai_agent import DineroAgent
                agent = DineroAgent()
                st.success("✅ AI Agent initialized successfully!")
            except Exception as e:
                st.error(f"❌ AI Agent error: {str(e)}")
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    import streamlit as st
    import pandas as pd
    import plotly
    
    system_info = {
        "Component": ["Streamlit", "Pandas", "Plotly", "Python"],
        "Version": [st.__version__, pd.__version__, plotly.__version__, "3.x"]
    }
    
    df_system = pd.DataFrame(system_info)
    st.dataframe(df_system, use_container_width=True)


def main():
    """Main application entry point."""
    
    st.title("� Dinero AI — AI Finance Agent for SMBs")
    st.caption("Your AI Accountant that monitors, decides, and acts.")
    
    # Initialize AI Agent (with error handling)
    try:
        agent = DineroAgent()
        agent_available = True
    except AIAgentError as e:
        st.warning(f"⚠️ AI Agent initialization failed: {str(e)}. Running in limited mode.")
        agent = None
        agent_available = False

    # ----------------------------
    # Navigation Tabs
    # ----------------------------
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "💾 Database", "👥 Clients", "⚙️ Settings"])
    
    with tab1:
    
        # ----------------------------
        # File Upload Section
        # ----------------------------
        uploaded_file = st.file_uploader("Upload Ledger CSV", type=["csv"])
        
        if uploaded_file:
            try:
                # Read CSV with error handling
                df = pd.read_csv(uploaded_file)
                
                # Validate ledger structure
                is_valid, errors = validate_ledger(df)
                
                if not is_valid:
                    st.error("❌ Invalid ledger format:")
                    for error in errors:
                        st.error(f"  • {error}")
                    st.info("Please ensure your CSV has columns: date, client, description, amount, type, status")
                    return
                
                # Clean and standardize data
                df = clean_dataframe(df)
                
                # ----------------------------
                # Duplicate Detection & Database Saving
                # ----------------------------
                # For now, use a default business_id (in production, this would come from user session)
                default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
                
                st.info("🔍 Checking for duplicates...")
                
                # Filter out duplicates
                new_transactions, duplicate_count = filter_duplicate_transactions(df, default_business_id)
                
                if duplicate_count > 0:
                    st.warning(f"⚠️ Found {duplicate_count} duplicate transactions - these will be skipped")
                
                if len(new_transactions) > 0:
                    st.success(f"✅ Found {len(new_transactions)} new transactions to save")
                    
                    # Save to Supabase database
                    with st.spinner("💾 Saving transactions to Supabase database..."):
                        try:
                            # Ensure default business exists
                            with db_session() as session:
                                business = session.query(Business).filter_by(id=default_business_id).first()
                                if not business:
                                    # Create default business for demo
                                    business = Business(
                                        id=default_business_id,
                                        business_name="Demo Business",
                                        currency_code='INR',
                                        is_active=True
                                    )
                                    session.add(business)
                                    session.commit()
                            
                            saved_count = save_transactions_to_database(new_transactions, default_business_id)
                            if saved_count > 0:
                                st.success(f"💾 Successfully saved {saved_count} new transactions to Supabase database")
                            else:
                                st.warning("⚠️ No transactions were saved")
                        except Exception as e:
                            st.error(f"❌ Error saving to database: {str(e)}")
                            logger.error(f"Database save error: {str(e)}")
                else:
                    if duplicate_count > 0:
                        st.info("ℹ️ All transactions in this file already exist in the database")
                    else:
                        st.info("ℹ️ No transactions to process")
                
                # Continue with original CSV data for display and analysis
                # (The display shows all data, but only new transactions were saved to database)
                
                # ----------------------------
                # GST Classification Engine
                # ----------------------------
                df["gst_category"] = df.apply(
                    lambda row: classify_gst(row["description"]) if row["type"] == "expense" else "",
                    axis=1
                )
                
                st.subheader("📄 Ledger Preview")
                st.dataframe(df, use_container_width=True)
                
                # ----------------------------
                # Financial Calculations
                # ----------------------------
                metrics = calculate_financials(df)
                health = assess_financial_health(metrics)
                
                # ----------------------------
                # Dashboard
                # ----------------------------
                st.subheader("📊 Financial Snapshot")
                
                # Health indicator
                health_colors = {"healthy": "🟢", "moderate": "🟡", "critical": "🔴"}
                st.markdown(f"**Financial Health:** {health_colors.get(health['status'], '⚪')} {health['status'].upper()} (Score: {health['score']}/100)")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Revenue", f"₹{metrics['revenue']:,.0f}")
                col2.metric("Expenses", f"₹{metrics['expenses']:,.0f}")
                col3.metric("Profit", f"₹{metrics['profit']:,.0f}", 
                           delta=f"{metrics['profit_margin']:.1f}% margin")
                col4.metric("Outstanding", f"₹{metrics['receivables']:,.0f}",
                           delta=f"{metrics['receivables_ratio']:.1f}% of revenue",
                           delta_color="inverse")
                
                # Pie chart
                fig = px.pie(df, names="type", values="amount", title="Income vs Expenses",
                                        color_discrete_map={"income": "#2ecc71", "expense": "#e74c3c"})
                st.plotly_chart(fig, use_container_width=True)
                
                # ----------------------------
                # GST Classification Display
                # ----------------------------
                gst_df = df[df["type"] == "expense"]
                
                st.subheader("🧾 GST Classification (India)")
                st.dataframe(gst_df[["date", "description", "amount", "gst_category"]], use_container_width=True)
                
                gst_summary = gst_df.groupby("gst_category")["amount"].sum().reset_index()
                gst_stats = get_gst_summary(gst_df)
                
                # GST Summary metrics
                col_itc, col_blocked, col_review = st.columns(3)
                col_itc.metric("ITC Eligible", f"₹{gst_stats['itc_eligible']:,.0f}")
                col_blocked.metric("Blocked/Non-Claimable", f"₹{gst_stats['blocked_credit'] + gst_stats['non_claimable']:,.0f}")
                col_review.metric("Needs Review", f"₹{gst_stats['review_required']:,.0f}")
                
                if not gst_summary.empty:
                    fig2 = px.bar(gst_summary, x="gst_category", y="amount",
                                  title="GST Credit Distribution", color="gst_category")
                    st.plotly_chart(fig2, use_container_width=True)
                
                # ----------------------------
                # Multi-Month Memory
                # ----------------------------
                st.subheader("💾 Save to Financial Memory")
                
                col_month, col_save = st.columns([3, 1])
                with col_month:
                    month_tag = st.text_input("Enter Month Label (e.g., Jan-2026)")
                with col_save:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    if st.button("Save This Month"):
                        # Validate month label
                        sanitized_label = sanitize_text_input(month_tag)
                        is_valid, error = validate_month_label(sanitized_label)
                        
                        if not is_valid:
                            st.warning(f"⚠️ {error}")
                        else:
                            entry = {
                                "month": sanitized_label,
                                "revenue": float(metrics["revenue"]),
                                "expenses": float(metrics["expenses"]),
                                "profit": float(metrics["profit"]),
                                "receivables": float(metrics["receivables"]),
                                "profit_margin": float(metrics["profit_margin"]),
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            if save_memory(entry):
                                st.success("Month saved to Dinero AI Memory ✅")
                            else:
                                st.error("Failed to save memory. Please check logs.")
                
                # ----------------------------
                # Financial Trend Visualization
                # ----------------------------
                history = load_memory()
                
                if len(history) > 1:
                    hist_df = pd.DataFrame(history)
                    
                    st.subheader("📈 Financial Trend (Multi-Month)")
                    
                    fig_trend = px.line(hist_df, x="month", y=["revenue", "expenses", "profit"],
                                        markers=True, title="Revenue, Expenses & Profit Over Time")
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # Receivables trend
                    fig_recv = px.bar(hist_df, x="month", y="receivables",
                                      title="Outstanding Receivables Trend", 
                                      color_discrete_sequence=["#FF6B6B"])
                    st.plotly_chart(fig_recv, use_container_width=True)
                elif len(history) == 1:
                    st.info("📊 Upload more months to see financial trends.")
                
                # ----------------------------
                # 🤖 AI AGENT (Reason → Decide → Act)
                # ----------------------------
                st.subheader("🤖 AI Agent Analysis")
                
                if not agent_available:
                    st.warning("AI Agent is not available. Please check your GEMINI_API_KEY.")
                
                if st.button("Run Dinero AI Agent", disabled=not agent_available):
                    with st.spinner("Dinero AI is analyzing your business..."):
                        try:
                            # Prepare context
                            financial_state = format_financial_state(metrics)
                            history_context = format_history_for_agent(get_recent_history(3))
                            gst_context = gst_summary.to_string(index=False) if not gst_summary.empty else "No GST data"
                            
                            # Run AI analysis
                            analysis = agent.analyze_financials(
                                financial_state=financial_state,
                                history_context=history_context,
                                gst_context=gst_context
                            )
                            
                            st.subheader("🧠 Agent Insight")
                            st.markdown(analysis)
                            
                        except Exception as e:
                            logger.error(f"Agent analysis failed: {str(e)}")
                            st.error(f"Analysis failed: {str(e)}. Please try again.")
                    
                    # ----------------------------
                    # Deterministic Rule-Based Actions
                    # ----------------------------
                    st.subheader("⚙️ Actions Taken by Dinero AI")
                    
                    # Display risk alerts
                    for risk in health["risks"]:
                        if risk["type"] == "critical":
                            st.error(f"🚨 {risk['message']}")
                            st.info(f"💡 Recommendation: {risk['recommendation']}")
                        else:
                            st.warning(f"⚠️ {risk['message']}")
                            st.info(f"💡 Recommendation: {risk['recommendation']}")
                    
                    # Generate reminder emails for overdue clients
                    if metrics["receivables_ratio"] > HIGH_RECEIVABLES_THRESHOLD * 100:
                        overdue_clients = get_overdue_clients(df)
                        
                        if overdue_clients:
                            st.markdown("### 📧 Payment Reminder Drafts")
                            
                            for client in overdue_clients[:3]:  # Limit to 3 to avoid API overload
                                with st.expander(f"Draft for {client}"):
                                    try:
                                        email = agent.generate_reminder_email(client)
                                        st.code(email, language=None)
                                    except Exception as e:
                                        st.error(f"Failed to generate email: {str(e)}")
                    
                        # Success case
                        if len(health["risks"]) == 0:
                            st.success("✅ Financial health stable. No immediate intervention needed.")
            
            except pd.errors.EmptyDataError:
                st.error("❌ The uploaded file is empty. Please upload a valid CSV.")
            except pd.errors.ParserError as e:
                st.error(f"❌ Failed to parse CSV: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                st.error(f"❌ An unexpected error occurred: {str(e)}")
                st.info("Please try again or contact support if the issue persists.")
        
        else:
            st.info("Upload a ledger CSV to activate Dinero AI.")
            
            # Show sample format
            with st.expander("📋 Sample CSV Format"):
                st.code("""date,client,description,amount,type,status
2026-01-01,ABC Corp,Website Project,50000,income,paid
2026-01-10,XYZ Ltd,Consulting,30000,income,unpaid
2026-01-12,AWS,AWS Cloud Subscription,12000,expense,paid
2026-01-15,Landlord,Office Rent,20000,expense,paid""")
    
    with tab2:
        display_database_tab()
    
    with tab3:
        display_clients_tab()
    
    with tab4:
        display_settings_tab()


if __name__ == "__main__":
    main()
