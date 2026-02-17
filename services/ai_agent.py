"""
AI Agent Service - Handles all LLM interactions with proper error handling and guardrails.
Implements responsible AI practices including validation, retries, and output sanitization.
"""
import google.generativeai as genai
import time
import json
import re
import logging
from typing import Optional, Dict, Any
from config.settings import (
    GEMINI_API_KEY, 
    GEMINI_MODEL, 
    MAX_API_RETRIES, 
    API_RETRY_DELAY
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAgentError(Exception):
    """Custom exception for AI Agent errors."""
    pass


class DineroAgent:
    """
    AI Agent for financial analysis and recommendations.
    Implements guardrails, validation, and responsible AI practices.
    """
    
    def __init__(self) -> None:
        """Initialize the AI agent with configuration.
        
        Raises:
            AIAgentError: If GEMINI_API_KEY is not configured
        """
        if not GEMINI_API_KEY:
            raise AIAgentError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        
        # System prompt for consistent behavior
        self.system_context = """
        You are Dinero AI, an AI accounting agent for Indian SMBs.
        
        GUIDELINES:
        - Provide specific, actionable financial advice
        - Reference Indian GST regulations accurately
        - Be conservative with financial projections
        - Flag uncertainties clearly
        - Never provide specific tax filing advice (recommend CA consultation)
        - Focus on operational recommendations
        """
    
    def _sanitize_output(self, text: str) -> str:
        """
        Sanitize AI output to remove potentially harmful content.
        
        Args:
            text: Raw AI response text
            
        Returns:
            Sanitized text
        """
        # Remove any potential script injections
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _validate_response(self, text: str) -> bool:
        """
        Validate AI response for quality and safety.
        
        Args:
            text: AI response text
            
        Returns:
            True if response is valid
        """
        if not text or len(text.strip()) < 50:
            return False
        
        # Check for common hallucination patterns
        hallucination_patterns = [
            r'as an ai',
            r'i cannot access',
            r'i don\'t have access',
            r'error occurred'
        ]
        
        for pattern in hallucination_patterns:
            if re.search(pattern, text.lower()):
                logger.warning(f"Potential hallucination detected: {pattern}")
                # Don't reject, just log - the response might still be useful
        
        return True
    
    def _call_with_retry(self, prompt: str) -> str:
        """
        Call the AI model with retry logic.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            AI response text
            
        Raises:
            AIAgentError: If all retries fail
        """
        last_error = None
        
        for attempt in range(MAX_API_RETRIES):
            try:
                response = self.model.generate_content(prompt)
                
                if response and response.text:
                    return response.text
                else:
                    raise AIAgentError("Empty response from AI model")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < MAX_API_RETRIES - 1:
                    time.sleep(API_RETRY_DELAY * (attempt + 1))  # Exponential backoff
        
        raise AIAgentError(f"Failed after {MAX_API_RETRIES} attempts: {str(last_error)}")
    
    def generate_executive_summary(self, financial_state: str, health: dict) -> str:
        """
        Generate executive summary of business financial position.
        
        Args:
            financial_state: Current financial data
            health: Financial health assessment
            
        Returns:
            Executive summary text
        """
        prompt = f"""
        {self.system_context}
        
        You are generating an EXECUTIVE SUMMARY for a business owner.
        
        CURRENT FINANCIAL DATA:
        {financial_state}
        
        FINANCIAL HEALTH ASSESSMENT:
        Status: {health.get('status', 'unknown')}
        Score: {health.get('score', 0)}/100
        Number of Risks: {len(health.get('risks', []))}
        
        INSTRUCTIONS:
        Write a concise 2-3 sentence executive summary that:
        1. Clearly states the overall financial position (healthy/moderate/critical)
        2. Highlights the most important metric or concern
        3. Provides a quick snapshot that a busy business owner can understand in 10 seconds
        
        Be direct, specific, and use actual numbers. Start with "Your business is currently..."
        
        Do NOT use section headers. Write in paragraph form.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"Executive summary generation failed: {str(e)}")
            return f"Your business shows {health.get('status', 'moderate')} financial health with a score of {health.get('score', 0)}/100. Review the detailed sections below for comprehensive analysis."
    
    def generate_financial_diagnosis(self, financial_state: str, metrics: dict) -> str:
        """
        Generate detailed financial diagnosis.
        
        Args:
            financial_state: Current financial data
            metrics: Calculated financial metrics
            
        Returns:
            Financial diagnosis text
        """
        prompt = f"""
        {self.system_context}
        
        You are performing a FINANCIAL DIAGNOSIS for an Indian SMB.
        
        CURRENT FINANCIAL DATA:
        {financial_state}
        
        KEY METRICS:
        - Revenue: ₹{metrics.get('revenue', 0):,.0f}
        - Expenses: ₹{metrics.get('expenses', 0):,.0f}
        - Profit: ₹{metrics.get('profit', 0):,.0f}
        - Profit Margin: {metrics.get('profit_margin', 0):.1f}%
        - Outstanding Receivables: ₹{metrics.get('receivables', 0):,.0f}
        - Receivables Ratio: {metrics.get('receivables_ratio', 0):.1f}%
        
        INSTRUCTIONS:
        Provide a detailed financial diagnosis covering:
        
        1. **Profitability Assessment:**
           - Is the business profitable? By how much?
           - Is the profit margin healthy for an Indian SMB (benchmark: 10-20%)?
           - Specific analysis of revenue vs expense ratio
        
        2. **Revenue Analysis:**
           - Revenue level assessment (adequate/strong/weak)
           - Any concerns about revenue concentration or sustainability?
        
        3. **Expense Analysis:**
           - Are expenses well-controlled or excessive?
           - Operating expense ratio analysis
        
        4. **Receivables Health:**
           - Outstanding receivables as % of revenue (healthy < 30%)
           - Collection efficiency assessment
           - Working capital implications
        
        Use bullet points. Be specific with numbers and percentages. Compare against industry benchmarks.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"Financial diagnosis failed: {str(e)}")
            return "Unable to generate detailed diagnosis. Please check the dashboard metrics manually."
    
    def generate_trend_analysis(self, financial_state: str, history_context: str) -> str:
        """
        Generate trend analysis comparing historical data.
        
        Args:
            financial_state: Current financial data
            history_context: Historical financial data
            
        Returns:
            Trend analysis text
        """
        prompt = f"""
        {self.system_context}
        
        You are analyzing FINANCIAL TRENDS over multiple months for an Indian SMB.
        
        CURRENT MONTH:
        {financial_state}
        
        HISTORICAL DATA (Past Months):
        {history_context}
        
        INSTRUCTIONS:
        Analyze trends and patterns:
        
        1. **Revenue Trends:**
           - Month-over-month growth or decline (calculate % change)
           - Growth trajectory (accelerating/stable/declining)
           - Seasonality patterns if visible
        
        2. **Expense Trends:**
           - Are expenses growing faster than revenue?
           - Any concerning expense drift or cost inflation?
           - Expense control effectiveness
        
        3. **Profit Margin Evolution:**
           - Is profit margin improving or eroding?
           - What's driving margin changes?
        
        4. **Receivables Trends:**
           - Is outstanding amount growing or shrinking?
           - Collection efficiency over time
        
        5. **Key Insights:**
           - Most significant trend (positive or negative)
           - Early warning signs if any
        
        If historical data is limited, clearly state that and provide what analysis is possible.
        Use percentages for changes. Use bullet points.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"Trend analysis failed: {str(e)}")
            return "Historical data analysis unavailable. Save more months to enable trend analysis."
    
    def generate_cashflow_analysis(self, metrics: dict, overdue_clients: list, df) -> str:
        """
        Generate cash flow risk analysis.
        
        Args:
            metrics: Financial metrics
            overdue_clients: List of clients with overdue payments
            df: Transaction dataframe
            
        Returns:
            Cash flow analysis text
        """
        # Calculate client concentration
        client_revenue = df[df['type'] == 'income'].groupby('client')['amount'].sum().sort_values(ascending=False)
        top_client_pct = (client_revenue.iloc[0] / client_revenue.sum() * 100) if len(client_revenue) > 0 else 0
        
        prompt = f"""
        {self.system_context}
        
        You are analyzing CASH FLOW RISKS for an Indian SMB.
        
        KEY DATA:
        - Outstanding Receivables: ₹{metrics.get('receivables', 0):,.0f}
        - Receivables as % of Revenue: {metrics.get('receivables_ratio', 0):.1f}%
        - Number of Overdue Clients: {len(overdue_clients)}
        - Overdue Clients: {', '.join(overdue_clients[:5]) if overdue_clients else 'None'}
        - Top Client Concentration: {top_client_pct:.1f}% of revenue
        - Current Profit: ₹{metrics.get('profit', 0):,.0f}
        
        INSTRUCTIONS:
        Analyze cash flow risks:
        
        1. **Receivables Risk:**
           - Is the receivables ratio healthy? (Benchmark: <30% is good, >50% is critical)
           - Impact on working capital and liquidity
           - Days Sales Outstanding estimate
        
        2. **Collection Risk:**
           - How many clients are overdue?
           - Severity assessment
           - Potential bad debt risk
        
        3. **Client Concentration Risk:**
           - Is revenue too concentrated in top client(s)? (>40% is risky)
           - Business continuity implications
           - Diversification recommendations
        
        4. **Working Capital Assessment:**
           - Can the business meet short-term obligations?
           - Cash flow adequacy for operations
        
        5. **Liquidity Concerns:**
           - Any immediate cash crunch indicators?
           - Runway analysis based on current profit
        
        Be specific about risk levels (low/moderate/high/critical). Use numbers and percentages.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"Cash flow analysis failed: {str(e)}")
            return "Cash flow analysis unavailable. Monitor your receivables and collection efficiency manually."
    
    def generate_gst_analysis(self, gst_context: str, gst_summary_df) -> str:
        """
        Generate GST structure and optimization analysis.
        
        Args:
            gst_context: GST classification summary
            gst_summary_df: GST summary dataframe
            
        Returns:
            GST analysis text
        """
        from services.gst_classifier import get_gst_summary
        import pandas as pd
        
        # Calculate GST stats if dataframe available
        gst_stats = {
            'itc_eligible': 0,
            'blocked_credit': 0,
            'non_claimable': 0,
            'review_required': 0
        }
        
        if isinstance(gst_summary_df, pd.DataFrame) and not gst_summary_df.empty:
            for _, row in gst_summary_df.iterrows():
                category = row.get('gst_category', '')
                amount = row.get('amount', 0)
                
                if 'ITC Eligible' in category:
                    gst_stats['itc_eligible'] += amount
                elif 'Blocked Credit' in category:
                    gst_stats['blocked_credit'] += amount
                elif 'Non-Claimable' in category:
                    gst_stats['non_claimable'] += amount
                elif 'Review' in category:
                    gst_stats['review_required'] += amount
        
        prompt = f"""
        {self.system_context}
        
        You are analyzing GST STRUCTURE and INPUT TAX CREDIT opportunities for an Indian SMB.
        
        GST CLASSIFICATION DATA:
        {gst_context}
        
        GST SUMMARY STATISTICS:
        - ITC Eligible Expenses: ₹{gst_stats['itc_eligible']:,.0f}
        - Blocked Credit Items: ₹{gst_stats['blocked_credit']:,.0f}
        - Non-Claimable Items: ₹{gst_stats['non_claimable']:,.0f}
        - Items Needing Review: ₹{gst_stats['review_required']:,.0f}
        
        INSTRUCTIONS:
        Provide detailed GST analysis:
        
        1. **Input Tax Credit (ITC) Assessment:**
           - Total ITC eligible amount and its significance
           - What % of total expenses can claim ITC?
           - Ensure timely ITC claiming to improve cash flow
        
        2. **Blocked Credit Analysis:**
           - What expenses have blocked credit and why?
           - Categories: rent, motor vehicles, food, entertainment, etc.
           - Are these expenses necessary despite no ITC benefit?
        
        3. **Non-Claimable Items:**
           - Items not eligible for GST ITC
           - Can some be restructured for ITC eligibility?
        
        4. **Items Requiring Review:**
           - Which expenses need CA review for proper classification?
           - Potential reclassification opportunities
        
        5. **GST Optimization Opportunities:**
           - How to maximize ITC claims legally?
           - Vendor GST compliance importance
           - Invoice and documentation best practices
        
        6. **Compliance Recommendations:**
           - GSTR filing reminders based on expense activity
           - Record maintenance suggestions
        
        Reference specific Indian GST rules (Section 17(5) for blocked credits, etc.).
        Be practical and actionable. Use bullet points.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"GST analysis failed: {str(e)}")
            return "GST analysis unavailable. Consult a CA for detailed ITC optimization."
    
    def generate_recommendations(self, financial_state: str, health: dict, history_context: str) -> str:
        """
        Generate actionable recommendations.
        
        Args:
            financial_state: Current financial data
            health: Financial health assessment
            history_context: Historical context
            
        Returns:
            Recommendations text
        """
        prompt = f"""
        {self.system_context}
        
        You are providing ACTIONABLE RECOMMENDATIONS for an Indian SMB owner.
        
        CURRENT SITUATION:
        {financial_state}
        
        HEALTH STATUS:
        Status: {health.get('status', 'unknown')}
        Score: {health.get('score', 0)}/100
        Identified Risks: {len(health.get('risks', []))}
        
        HISTORICAL CONTEXT:
        {history_context}
        
        INSTRUCTIONS:
        Provide specific, actionable recommendations in these categories:
        
        1. **Revenue Enhancement:**
           - How to increase revenue based on current trends
           - New revenue stream suggestions
           - Client acquisition vs retention strategies
        
        2. **Cost Optimization:**
           - Which expense categories to review/reduce
           - Specific cost-cutting opportunities without hurting operations
           - Vendor negotiation suggestions
        
        3. **Cash Flow Improvement:**
           - Invoice payment terms optimization
           - Collection process improvements
           - Working capital management tactics
        
        4. **Financial Health Improvement:**
           - Priority actions to improve financial health score
           - Metric targets to aim for (profit margin, receivables ratio, etc.)
        
        5. **Process Improvements:**
           - Accounting and bookkeeping best practices
           - Financial monitoring frequency
           - KPI tracking recommendations
        
        6. **Risk Mitigation:**
           - How to address identified risks
           - Contingency planning
        
        Make each recommendation:
        - Specific (not generic)
        - Actionable (clear next steps)
        - Measurable (with targets where possible)
        - Realistic for an Indian SMB
        
        Use numbered sub-points for clarity.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"Recommendations generation failed: {str(e)}")
            return "Unable to generate recommendations. Review dashboard alerts for system-generated suggestions."
    
    def generate_urgent_actions(self, health: dict, metrics: dict, overdue_clients: list) -> str:
        """
        Generate urgent actions needed.
        
        Args:
            health: Financial health assessment
            metrics: Financial metrics
            overdue_clients: List of overdue clients
            
        Returns:
            Urgent actions text
        """
        risks = health.get('risks', [])
        critical_risks = [r for r in risks if r.get('type') == 'critical']
        
        prompt = f"""
        {self.system_context}
        
        You are identifying URGENT ACTIONS for an Indian SMB.
        
        CRITICAL SITUATION INDICATORS:
        - Financial Health Score: {health.get('score', 0)}/100
        - Status: {health.get('status', 'unknown')}
        - Critical Risks Count: {len(critical_risks)}
        - Overdue Clients: {len(overdue_clients)}
        - Receivables Ratio: {metrics.get('receivables_ratio', 0):.1f}%
        - Profit Margin: {metrics.get('profit_margin', 0):.1f}%
        
        IDENTIFIED RISKS:
        {chr(10).join([f"- {r.get('message', '')} ({r.get('type', 'unknown')})" for r in risks]) if risks else "No specific risks identified"}
        
        INSTRUCTIONS:
        Identify urgent actions that need IMMEDIATE attention (within 1-7 days):
        
        1. **High Priority (Do Today):**
           - Actions that must be taken immediately
           - Critical payment follow-ups
           - Urgent cash flow needs
        
        2. **Medium Priority (This Week):**
           - Important but can wait a few days
           - Process improvements needed soon
        
        3. **Follow-up Actions:**
           - Specific clients to contact
           - Invoices to send
           - Documents to prepare
        
        4. **Deadlines & Commitments:**
           - Any upcoming GST filing deadlines
           - Payment commitments to monitor
           - Critical vendor payments
        
        If there are NO urgent actions (business is healthy), clearly state:
        "No urgent actions required. Business is operating smoothly. Focus on the recommendations for continuous improvement."
        
        Be direct and specific. Use action verbs. Format as a prioritized checklist.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"Urgent actions generation failed: {str(e)}")
            if critical_risks:
                return f"URGENT: Address {len(critical_risks)} critical risks shown in the Dashboard tab immediately."
            else:
                return "No urgent actions required at this time. Continue monitoring your financial health regularly."
    
    def generate_reminder_email(self, client_name: str, amount: float = None) -> str:
        """
        Generate a payment reminder email for a client.
        
        Args:
            client_name: Name of the client
            amount: Outstanding amount (optional)
            
        Returns:
            Email draft text
        """
        amount_text = f" of ₹{amount:,.2f}" if amount else ""
        
        prompt = f"""
        Write a polite but firm payment reminder email to {client_name}
        regarding an overdue invoice{amount_text}.
        
        Requirements:
        - Professional tone
        - Brief (under 150 words)
        - Include specific ask for payment timeline
        - Offer to discuss if there are concerns
        
        Return only the email body, no subject line.
        """
        
        try:
            response = self._call_with_retry(prompt)
            return self._sanitize_output(response)
        except AIAgentError as e:
            logger.error(f"Email generation failed: {str(e)}")
            return self._get_fallback_email(client_name)
    
    def _get_fallback_analysis(self) -> str:
        """Return fallback analysis when AI fails."""
        return """
**EXECUTIVE SUMMARY:**
The AI analysis service is temporarily unavailable. Please review the dashboard metrics for manual analysis.

**FINANCIAL DIAGNOSIS:**
- Check the Dashboard tab for current revenue, expenses, and profit metrics
- Review the financial health score and status indicator
- Compare outstanding receivables against revenue percentage

**TREND ANALYSIS:**
- Visit the Trends tab to view historical performance
- Look for month-over-month changes in key metrics
- Identify any unusual spikes or drops in revenue/expenses

**CASH FLOW RISKS:**
- Review system alerts on the Dashboard tab for identified risks
- Check client concentration in receivables
- Monitor payment collection timelines

**GST ANALYSIS:**
- Navigate to GST Analysis tab for detailed breakdown
- Review ITC eligible vs blocked credit amounts
- Check expenses marked for GST review

**RECOMMENDATIONS:**
- Follow up on unpaid invoices to improve cash flow
- Review expenses marked for GST review with your CA
- Monitor the system-generated alerts and act on recommendations
- Maintain regular month-over-month comparisons

**URGENT ACTIONS:**
- Address any critical alerts shown on the Dashboard
- Consult a Chartered Accountant for detailed tax planning
- Re-run the AI analysis once the service is available

*This is a fallback response. Please try again later for AI-powered insights.*
        """
    
    def _get_fallback_email(self, client_name: str) -> str:
        """Return fallback email template when AI fails."""
        return f"""
Dear {client_name},

I hope this email finds you well.

This is a friendly reminder regarding the outstanding payment on your account. 
We would appreciate it if you could process the payment at your earliest convenience.

If you have any questions or concerns, please don't hesitate to reach out.

Thank you for your continued business.

Best regards,
[Your Company Name]
        """.strip()
