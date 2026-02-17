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
    
    def __init__(self):
        """Initialize the AI agent with configuration."""
        if not GEMINI_API_KEY:
            raise AIAgentError("GEMINI_API_KEY not found in environment variables")
        
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
    
    def analyze_financials(
        self, 
        financial_state: str, 
        history_context: str = "No past data available",
        gst_context: str = "No GST data"
    ) -> str:
        """
        Perform comprehensive financial analysis.
        
        Args:
            financial_state: Current month financial data
            history_context: Historical financial data (JSON string)
            gst_context: GST classification summary
            
        Returns:
            AI analysis and recommendations
        """
        prompt = f"""
        {self.system_context}

        CURRENT MONTH DATA:
        {financial_state}

        PAST MONTHS (Recent History):
        {history_context}

        GST EXPENSE STRUCTURE:
        {gst_context}

        ANALYSIS REQUIRED:
        1. Diagnose current financial condition
        2. Compare with past months - detect growth/decline trends, expense drift
        3. Identify cashflow risks forming over time
        4. Analyze GST structure - identify missed ITC opportunities
        5. Provide specific, actionable recommendations
        6. Highlight any urgent actions needed

        Format your response with clear sections and bullet points.
        Be specific with numbers and percentages.
        """
        
        try:
            response = self._call_with_retry(prompt)
            sanitized = self._sanitize_output(response)
            
            if not self._validate_response(sanitized):
                return self._get_fallback_analysis()
            
            return sanitized
            
        except AIAgentError as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._get_fallback_analysis()
    
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
        ⚠️ **Automated Analysis Unavailable**
        
        The AI analysis service is temporarily unavailable. Please review the metrics manually:
        
        **Key Areas to Check:**
        - Compare revenue vs expenses for profitability
        - Review outstanding receivables percentage
        - Check client concentration risk
        - Verify GST ITC eligibility for expenses
        
        **Recommended Actions:**
        - Follow up on unpaid invoices
        - Review expenses marked for GST review
        - Consider consulting a CA for detailed analysis
        
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
