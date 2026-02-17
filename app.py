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
from utils.memory import load_memory, save_memory, get_recent_history, format_history_for_agent, ensure_memory_dir
from utils.validators import validate_ledger, clean_dataframe, sanitize_text_input, validate_month_label

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)

# Ensure memory directory exists
ensure_memory_dir()


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


if __name__ == "__main__":
    main()
