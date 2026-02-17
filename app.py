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
from datetime import datetime

# Local imports
from config.settings import PAGE_TITLE, PAGE_LAYOUT, HIGH_RECEIVABLES_THRESHOLD, CLIENT_CONCENTRATION_THRESHOLD
from services.gst_classifier import classify_gst, get_gst_summary
from services.financial_engine import calculate_financials, get_overdue_clients, assess_financial_health, format_financial_state
from services.ai_agent import DineroAgent, AIAgentError
from services.chatbot import FinancialChatbot
from utils.memory import load_memory, save_memory, get_recent_history, format_history_for_agent, ensure_memory_dir
from utils.validators import validate_ledger, clean_dataframe, sanitize_text_input, validate_month_label
from utils.time_periods import segment_by_period, get_period_metrics, compare_periods, get_available_periods, format_period_label
from utils.enhanced_memory import save_period_data, load_period_data, get_all_periods, auto_save_periods, get_financial_context, ensure_memory_dirs
from utils.pdf_generator import create_monthly_pdf_report
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_gst_knowledge() -> str:
    """
    Load GST knowledge base for AI agent context.
    
    Returns:
        GST rules text content, or empty string if file not found
    """
    try:
        knowledge_path = "knowledge/gst_rules.txt"
        with open(knowledge_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("GST knowledge base file not found. Agent will proceed without GST context.")
        return ""
    except Exception as e:
        logger.error(f"Error loading GST knowledge: {e}")
        return ""


def display_structured_analysis(analysis: str):
    """
    Parse and display AI analysis in a structured format with standardized subsections.
    
    Args:
        analysis: Raw AI analysis text
    """
    # Define section patterns
    sections = {
        "Executive Summary": r"(?i)(executive summary|summary|overview):?\s*(.+?)(?=\n\n|\n#|$)",
        "Financial Diagnosis": r"(?i)(financial (diagnosis|condition|health)|diagnosis):?\s*(.+?)(?=\n\n|\n#|$)",
        "Trend Analysis": r"(?i)(trend analysis|trends|growth analysis|historical comparison):?\s*(.+?)(?=\n\n|\n#|$)",
        "Cash Flow Risks": r"(?i)(cash ?flow (risks?|issues?)|risks?):?\s*(.+?)(?=\n\n|\n#|$)",
        "GST Analysis": r"(?i)(gst (analysis|structure|opportunities)|input tax credit):?\s*(.+?)(?=\n\n|\n#|$)",
        "Recommendations": r"(?i)(recommendations?|action items?|next steps?):?\s*(.+?)(?=\n\n|\n#|$)",
        "Urgent Actions": r"(?i)(urgent actions?|immediate actions?|priority):?\s*(.+?)(?=\n\n|\n#|$)"
    }
    
    # Try to extract structured sections
    extracted_sections = {}
    
    for section_name, pattern in sections.items():
        match = re.search(pattern, analysis, re.DOTALL | re.MULTILINE)
        if match:
            # Get the content (last group in the match)
            content = match.group(match.lastindex).strip()
            extracted_sections[section_name] = content
    
    # If we successfully extracted sections, display them structured
    if len(extracted_sections) >= 3:
        for section_name, content in extracted_sections.items():
            with st.expander(f"📌 {section_name}", expanded=(section_name in ["Executive Summary", "Urgent Actions"])):
                st.markdown(content)
    else:
        # Fallback: try to split by numbered sections or headers
        lines = analysis.split('\n')
        current_section = "Analysis"
        current_content = []
        
        # Look for section headers (lines that start with numbers, *, or are ALL CAPS)
        for line in lines:
            # Check if line is a header
            is_header = False
            clean_line = line.strip()
            
            if clean_line:
                # Numbered header (1., 2., etc.)
                if re.match(r'^\d+\.\s+[A-Z]', clean_line):
                    is_header = True
                # All caps header
                elif clean_line.isupper() and len(clean_line) > 5:
                    is_header = True
                # Header with ** markdown
                elif clean_line.startswith('**') and clean_line.endswith('**'):
                    is_header = True
                    clean_line = clean_line.strip('*').strip()
            
            if is_header and current_content:
                # Display previous section
                with st.expander(f"📌 {current_section}", expanded=True):
                    st.markdown('\n'.join(current_content))
                current_section = clean_line
                current_content = []
            else:
                current_content.append(line)
        
        # Display last section
        if current_content:
            with st.expander(f"📌 {current_section}", expanded=True):
                st.markdown('\n'.join(current_content))
        
        # If still no structure, just display as-is
        if not current_content and not extracted_sections:
            st.markdown(analysis)

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)

# Ensure all memory directories exist
ensure_memory_dir()
ensure_memory_dirs()

# Initialize session state for chatbot
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []


def main():
    """Main application entry point."""
    
    # Navigation bar/header
    st.markdown("""
    <div style='background-color: #1f77b4; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>💰 Dinero AI</h1>
        <p style='color: #e0e0e0; margin: 5px 0 0 0;'>Your AI Accountant that monitors, decides, and acts</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize AI Agent (with error handling)
    gst_knowledge = load_gst_knowledge()
    try:
        agent = DineroAgent(gst_knowledge=gst_knowledge)
        agent_available = True
    except AIAgentError as e:
        st.warning("⚠️ AI analysis features are currently unavailable. System running in limited mode.")
        logger.error(f"AI Agent initialization failed: {str(e)}")
        agent = None
        agent_available = False
    
    # ----------------------------
    # File Upload Section
    # ----------------------------
    uploaded_file = st.file_uploader("📤 Upload Ledger CSV", type=["csv"])
    
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
            # GST Classification Engine
            # ----------------------------
            df["gst_category"] = df.apply(
                lambda row: classify_gst(row["description"], row["amount"]) if row["type"] == "expense" else "",
                axis=1
            )
            
            # ----------------------------
            # Time-Based Segmentation & Auto-Save
            # ----------------------------
            # Segment data by different time periods
            monthly_segments = segment_by_period(df, 'month')
            weekly_segments = segment_by_period(df, 'week')
            daily_segments = segment_by_period(df, 'day')
            yearly_segments = segment_by_period(df, 'year')
            
            # Auto-save all periods
            auto_save_periods(df, monthly_segments, 'month')
            auto_save_periods(df, weekly_segments, 'week')
            auto_save_periods(df, daily_segments, 'day')
            auto_save_periods(df, yearly_segments, 'year')
            
            # ----------------------------
            # Financial Calculations
            # ----------------------------
            metrics = calculate_financials(df)
            health = assess_financial_health(metrics)
            
            # Initialize chatbot with agent
            if agent_available and st.session_state.chatbot is None:
                st.session_state.chatbot = FinancialChatbot(agent)
            
            # ----------------------------
            # TAB-BASED NAVIGATION
            # ----------------------------
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📊 Dashboard",
                "🤖 AI Chatbot",
                "📊 AI Analysis",
                "🧾 GST Analysis",
                "📈 Trends & History",
                "📄 Ledger Data"
            ])
            
            # ----------------------------
            # TAB 1: DASHBOARD
            # ----------------------------
            with tab1:
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
                st.plotly_chart(fig, width='stretch')
                
                # Display risk alerts
                st.subheader("⚙️ System Alerts & Actions")
                for risk in health["risks"]:
                    if risk["type"] == "critical":
                        st.error(f"🚨 {risk['message']}")
                        st.info(f"💡 Recommendation: {risk['recommendation']}")
                    else:
                        st.warning(f"⚠️ {risk['message']}")
                        st.info(f"💡 Recommendation: {risk['recommendation']}")
                
                if len(health["risks"]) == 0:
                    st.success("✅ Financial health stable. No immediate intervention needed.")
            
            # ----------------------------
            # TAB 2: AI CHATBOT
            # ----------------------------
            with tab2:
                st.subheader("💬 Financial Assistant Chatbot")
                st.caption("Ask questions about your financial data. The AI has context of all your saved financial history.")
                
                if not agent_available:
                    st.warning("AI chatbot is currently unavailable. Please verify configuration.")
                else:
                    # Get financial context for chatbot
                    financial_context = get_financial_context('month', 12)
                    current_context = format_financial_state(metrics)
                    full_context = f"{current_context}\n\n{financial_context}"
                    
                    # Display chat messages
                    for msg in st.session_state.chat_messages:
                        with st.chat_message("user"):
                            st.write(msg["question"])
                        with st.chat_message("assistant"):
                            st.write(msg["answer"])
                    
                    # Chat input
                    user_question = st.chat_input("Ask me anything about your finances...")
                    
                    if user_question:
                        # Display user message
                        with st.chat_message("user"):
                            st.write(user_question)
                        
                        # Get AI response
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                response = st.session_state.chatbot.chat(user_question, full_context)
                                st.write(response)
                        
                        # Save to session state
                        st.session_state.chat_messages.append({
                            "question": user_question,
                            "answer": response
                        })
                    
                    # Clear chat button
                    if st.button("🗑️ Clear Chat History"):
                        st.session_state.chat_messages = []
                        st.session_state.chatbot.clear_history()
                        st.rerun()
            
            # ----------------------------
            # TAB 3: AI ANALYSIS WITH SEPARATE BUTTONS
            # ----------------------------
            with tab3:
                st.subheader("📊 Detailed AI Analysis")
                st.caption("Each section can be analyzed independently. Click buttons to generate specific insights.")
                
                if not agent_available:
                    st.warning("AI analysis is currently unavailable. Please verify configuration.")
                else:
                    # Prepare context data
                    financial_state = format_financial_state(metrics)
                    history_context = format_history_for_agent(get_recent_history(3))
                    gst_summary_df = df[df["type"] == "expense"].groupby("gst_category")["amount"].sum().reset_index()
                    gst_context = gst_summary_df.to_string(index=False) if not gst_summary_df.empty else "No GST data"
                    overdue_clients = get_overdue_clients(df)
                    
                    # Create columns for buttons
                    col1, col2, col3 = st.columns(3)
                    col4, col5, col6 = st.columns(3)
                    col7, col8, col9 = st.columns(3)
                    
                    # Section buttons
                    run_summary = col1.button("📝 Executive Summary", use_container_width=True)
                    run_diagnosis = col2.button("🏥 Financial Diagnosis", use_container_width=True)
                    run_trends = col3.button("📈 Trend Analysis", use_container_width=True)
                    run_cashflow = col4.button("💰 Cash Flow Risks", use_container_width=True)
                    run_gst = col5.button("🧾 GST Analysis", use_container_width=True)
                    run_recommendations = col6.button("💡 Recommendations", use_container_width=True)
                    run_urgent = col7.button("🚨 Urgent Actions", use_container_width=True)
                    run_all = col8.button("🚀 Run All", type="primary", use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Execute analysis based on button clicks
                    if run_summary or run_all:
                        with st.expander("📝 Executive Summary", expanded=True):
                            with st.spinner("Analyzing..."):
                                try:
                                    summary = agent.generate_executive_summary(financial_state, health)
                                    st.markdown(summary)
                                except Exception as e:
                                    st.error(f"Analysis failed: {str(e)}")
                    
                    if run_diagnosis or run_all:
                        with st.expander("🏥 Financial Diagnosis", expanded=True):
                            with st.spinner("Analyzing..."):
                                try:
                                    diagnosis = agent.generate_financial_diagnosis(financial_state, metrics)
                                    st.markdown(diagnosis)
                                except Exception as e:
                                    st.error(f"Analysis failed: {str(e)}")
                    
                    if run_trends or run_all:
                        with st.expander("📈 Trend Analysis", expanded=True):
                            with st.spinner("Analyzing..."):
                                try:
                                    trends = agent.generate_trend_analysis(financial_state, history_context)
                                    st.markdown(trends)
                                except Exception as e:
                                    st.error(f"Analysis failed: {str(e)}")
                    
                    if run_cashflow or run_all:
                        with st.expander("💰 Cash Flow Risks", expanded=True):
                            with st.spinner("Analyzing..."):
                                try:
                                    cash_flow = agent.generate_cashflow_analysis(metrics, overdue_clients, df)
                                    st.markdown(cash_flow)
                                except Exception as e:
                                    st.error(f"Analysis failed: {str(e)}")
                    
                    if run_gst or run_all:
                        with st.expander("🧾 GST Analysis", expanded=True):
                            with st.spinner("Analyzing..."):
                                try:
                                    gst_analysis = agent.generate_gst_analysis(gst_context, gst_summary_df)
                                    st.markdown(gst_analysis)
                                except Exception as e:
                                    st.error(f"Analysis failed: {str(e)}")
                    
                    if run_recommendations or run_all:
                        with st.expander("💡 Recommendations", expanded=True):
                            with st.spinner("Analyzing..."):
                                try:
                                    recommendations = agent.generate_recommendations(financial_state, health, history_context)
                                    st.markdown(recommendations)
                                except Exception as e:
                                    st.error(f"Analysis failed: {str(e)}")
                    
                    if run_urgent or run_all:
                        with st.expander("🚨 Urgent Actions", expanded=True):
                            with st.spinner("Analyzing..."):
                                try:
                                    urgent = agent.generate_urgent_actions(health, metrics, overdue_clients)
                                    st.markdown(urgent)
                                except Exception as e:
                                    st.error(f"Analysis failed: {str(e)}")
                    
                    # Payment reminder emails
                    if metrics["receivables_ratio"] > HIGH_RECEIVABLES_THRESHOLD * 100:
                        if overdue_clients and run_all:
                            st.markdown("---")
                            st.markdown("### 📧 Payment Reminder Drafts")
                            
                            for client in overdue_clients[:3]:
                                with st.expander(f"Draft for {client}"):
                                    with st.spinner("Generating..."):
                                        try:
                                            email = agent.generate_reminder_email(client)
                                            st.code(email, language=None)
                                        except Exception as e:
                                            st.error(f"Generation failed: {str(e)}")
            
            # ----------------------------
            # TAB 4: GST ANALYSIS
            # ----------------------------
            with tab4:
                gst_df = df[df["type"] == "expense"]
                
                st.subheader("🧾 GST Classification (India)")
                
                gst_summary = gst_df.groupby("gst_category")["amount"].sum().reset_index()
                gst_stats = get_gst_summary(gst_df)
                
                # GST Summary metrics
                col_itc, col_blocked, col_review = st.columns(3)
                col_itc.metric("ITC Eligible", f"₹{gst_stats['itc_eligible']:,.0f}")
                col_blocked.metric("Blocked/Non-Claimable", f"₹{gst_stats['blocked_credit'] + gst_stats['non_applicable']:,.0f}")
                col_review.metric("Needs Review", f"₹{gst_stats['review_required']:,.0f}")
                
                if not gst_summary.empty:
                    fig2 = px.bar(gst_summary, x="gst_category", y="amount",
                                  title="GST Credit Distribution", color="gst_category")
                    st.plotly_chart(fig2, width='stretch')
                
                st.markdown("---")
                st.markdown("### Detailed GST Breakdown")
                st.dataframe(gst_df[["date", "description", "amount", "gst_category"]], width='stretch')
            
            # ----------------------------
            # TAB 5: TRENDS & HISTORY WITH TIME PERIODS
            # ----------------------------
            with tab5:
                st.subheader("📈 Financial Trends & History")
                
                # Time period selector
                col_period_select, col_pdf_download = st.columns([3, 1])
                
                with col_period_select:
                    period_type = st.selectbox(
                        "View by:",
                        options=["Month", "Week", "Day", "Year"],
                        index=0
                    )
                
                period_type_key = period_type.lower()
                
                # Get saved periods
                all_periods = get_all_periods(period_type_key)
                
                # PDF Download Button
                with col_pdf_download:
                    if all_periods and period_type_key == 'month':
                        st.write("")
                        selected_period = st.selectbox(
                            "Select Period:",
                            options=[p['period'] for p in all_periods],
                            index=len(all_periods)-1,
                            key="pdf_period_select"
                        )
                        
                        # Get selected period data
                        period_data = next((p for p in all_periods if p['period'] == selected_period), None)
                        
                        if period_data:
                            # Get GST data for the selected period if available
                            gst_stats = None
                            if not df[df["type"] == "expense"].empty:
                                gst_df = classify_gst(df[df["type"] == "expense"])
                                gst_stats = get_gst_summary(gst_df)
                            
                            # Generate PDF
                            try:
                                pdf_buffer = create_monthly_pdf_report(
                                    period_label=selected_period,
                                    metrics={
                                        'revenue': period_data.get('revenue', 0),
                                        'expenses': period_data.get('expenses', 0),
                                        'profit': period_data.get('profit', 0),
                                        'profit_margin': period_data.get('profit_margin', 0),
                                        'receivables': period_data.get('receivables', 0),
                                        'receivables_ratio': period_data.get('receivables_ratio', 0),
                                        'top_client_name': period_data.get('top_client_name', 'N/A'),
                                        'top_client_share': period_data.get('top_client_share', 0)
                                    },
                                    health={
                                        'score': period_data.get('health_score', 0),
                                        'status': 'healthy' if period_data.get('health_score', 0) >= 80 else 'moderate' if period_data.get('health_score', 0) >= 60 else 'critical',
                                        'risks': []
                                    },
                                    periods_df=pd.DataFrame(all_periods),
                                    gst_stats=gst_stats
                                )
                                
                                st.download_button(
                                    label="📄 Download PDF",
                                    data=pdf_buffer,
                                    file_name=f"financial_statement_{selected_period}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    type="primary"
                                )
                            except Exception as e:
                                logger.error(f"PDF generation error: {str(e)}")
                                st.error(f"⚠️ PDF generation unavailable. Install required packages: pip install reportlab kaleido")
                    elif all_periods and period_type_key != 'month':
                        st.info("📄 PDF download available for Monthly view only")
                
                if all_periods:
                    # Convert to DataFrame for visualization
                    periods_df = pd.DataFrame(all_periods)
                    
                    # Time series charts
                    st.markdown(f"### {period_type}ly Performance")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_rev_exp = px.line(
                            periods_df,
                            x="period",
                            y=["revenue", "expenses"],
                            title=f"Revenue vs Expenses ({period_type}ly)",
                            markers=True,
                            labels={"value": "Amount (₹)", "variable": "Type"}
                        )
                        st.plotly_chart(fig_rev_exp, width='stretch')
                    
                    with col2:
                        fig_profit = px.bar(
                            periods_df,
                            x="period",
                            y="profit",
                            title=f"Profit Trend ({period_type}ly)",
                            color="profit",
                            color_continuous_scale=["red", "yellow", "green"]
                        )
                        st.plotly_chart(fig_profit, width='stretch')
                    
                    # Receivables and margin charts
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        fig_recv = px.area(
                            periods_df,
                            x="period",
                            y="receivables",
                            title=f"Outstanding Receivables ({period_type}ly)",
                            color_discrete_sequence=["#FF6B6B"]
                        )
                        st.plotly_chart(fig_recv, width='stretch')
                    
                    with col4:
                        fig_margin = px.line(
                            periods_df,
                            x="period",
                            y="profit_margin",
                            title=f"Profit Margin (%) ({period_type}ly)",
                            markers=True,
                            color_discrete_sequence=["#3498db"]
                        )
                        fig_margin.add_hline(y=10, line_dash="dash", line_color="green", annotation_text="Target: 10%")
                        st.plotly_chart(fig_margin, width='stretch')
                    
                    # Period comparison
                    st.markdown("---")
                    st.markdown("### Period Comparison")
                    
                    if len(all_periods) >= 2:
                        col_period1, col_period2, col_compare = st.columns([2, 2, 1])
                        
                        with col_period1:
                            period1 = st.selectbox(
                                "Compare Period 1:",
                                options=[p['period'] for p in all_periods],
                                index=len(all_periods)-2
                            )
                        
                        with col_period2:
                            period2 = st.selectbox(
                                "with Period 2:",
                                options=[p['period'] for p in all_periods],
                                index=len(all_periods)-1
                            )
                        
                        with col_compare:
                            st.write("")
                            st.write("")
                            show_comparison = st.button("📊 Compare", type="primary")
                        
                        if show_comparison:
                            p1_data = next((p for p in all_periods if p['period'] == period1), None)
                            p2_data = next((p for p in all_periods if p['period'] == period2), None)
                            
                            if p1_data and p2_data:
                                comparison = compare_periods(p2_data, p1_data)
                                
                                st.markdown(f"#### {period1} vs {period2}")
                                
                                comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)
                                
                                with comp_col1:
                                    rev_change = comparison['revenue_change']
                                    rev_pct = comparison['revenue_pct_change']
                                    st.metric(
                                        "Revenue",
                                        f"₹{p2_data['revenue']:,.0f}",
                                        delta=f"₹{rev_change:,.0f} ({rev_pct:+.1f}%)"
                                    )
                                
                                with comp_col2:
                                    exp_change = comparison['expenses_change']
                                    exp_pct = comparison['expenses_pct_change']
                                    st.metric(
                                        "Expenses",
                                        f"₹{p2_data['expenses']:,.0f}",
                                        delta=f"₹{exp_change:,.0f} ({exp_pct:+.1f}%)",
                                        delta_color="inverse"
                                    )
                                
                                with comp_col3:
                                    profit_change = comparison['profit_change']
                                    profit_pct = comparison['profit_pct_change']
                                    st.metric(
                                        "Profit",
                                        f"₹{p2_data['profit']:,.0f}",
                                        delta=f"₹{profit_change:,.0f} ({profit_pct:+.1f}%)"
                                    )
                                
                                with comp_col4:
                                    margin_change = comparison['profit_margin_change']
                                    st.metric(
                                        "Profit Margin",
                                        f"{p2_data['profit_margin']:.1f}%",
                                        delta=f"{margin_change:+.1f}%"
                                    )
                    else:
                        st.info("Need at least 2 periods for comparison. Upload more data!")
                
                else:
                    st.info(f"No {period_type_key}ly data saved yet. Data is automatically saved when you upload your ledger.")
            
            # ----------------------------
            # TAB 6: LEDGER DATA WITH FILTERING
            # ----------------------------
            with tab6:
                st.subheader("📄 Transaction Ledger")
                
                # Filters
                col_filter1, col_filter2, col_filter3 = st.columns(3)
                
                with col_filter1:
                    filter_type = st.multiselect(
                        "Transaction Type:",
                        options=df['type'].unique().tolist(),
                        default=df['type'].unique().tolist()
                    )
                
                with col_filter2:
                    filter_status = st.multiselect(
                        "Status:",
                        options=df['status'].unique().tolist(),
                        default=df['status'].unique().tolist()
                    )
                
                with col_filter3:
                    # Get available periods for filtering
                    available_periods = get_available_periods(df, 'month')
                    if available_periods:
                        filter_period = st.multiselect(
                            "Month:",
                            options=available_periods,
                            default=available_periods
                        )
                    else:
                        filter_period = []
                
                # Apply filters
                filtered_df = df.copy()
                
                if filter_type:
                    filtered_df = filtered_df[filtered_df['type'].isin(filter_type)]
                
                if filter_status:
                    filtered_df = filtered_df[filtered_df['status'].isin(filter_status)]
                
                if filter_period:
                    filtered_df['month'] = pd.to_datetime(filtered_df['date']).dt.strftime('%Y-%m')
                    filtered_df = filtered_df[filtered_df['month'].isin(filter_period)]
                    filtered_df = filtered_df.drop(columns=['month'])
                
                # Display metrics for filtered data
                st.markdown("### Filtered Data Summary")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                filtered_metrics = calculate_financials(filtered_df)
                
                metric_col1.metric("Transactions", len(filtered_df))
                metric_col2.metric("Total Income", f"₹{filtered_metrics['revenue']:,.0f}")
                metric_col3.metric("Total Expenses", f"₹{filtered_metrics['expenses']:,.0f}")
                
                # Display data
                st.markdown("---")
                st.dataframe(filtered_df, width='stretch', height=400)
                
                # Download button
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data",
                    data=csv,
                    file_name=f"ledger_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        
        except pd.errors.EmptyDataError:
            st.error("❌ The uploaded file is empty. Please upload a valid CSV.")
        except pd.errors.ParserError as e:
            st.error(f"❌ Failed to parse CSV: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            st.error(f"❌ An error occurred: {str(e)}")
    
    else:
        st.info("Upload your ledger CSV to begin financial analysis.")
        
        # Show sample format
        with st.expander("📋 Sample CSV Format"):
            st.code("""date,client,description,amount,type,status
2026-01-01,ABC Corp,Website Project,50000,income,paid
2026-01-10,XYZ Ltd,Consulting,30000,income,unpaid
2026-01-12,AWS,AWS Cloud Subscription,12000,expense,paid
2026-01-15,Landlord,Office Rent,20000,expense,paid""")


if __name__ == "__main__":
    main()
