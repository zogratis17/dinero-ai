"""
AI Financial Chatbot with guardrails and context awareness.
Handles user queries about financial data with proper security measures.
"""
import re
import logging
from typing import Optional, Tuple, List, Dict, Any
from services.ai_agent import AIAgentError

logger = logging.getLogger(__name__)


class FinancialChatbot:
    """
    Secure financial chatbot with guardrails and prompt injection prevention.
    """
    
    def __init__(self, agent) -> None:
        """Initialize chatbot with AI agent.
        
        Args:
            agent: DineroAgent instance for AI interactions
        """
        self.agent = agent
        self.conversation_history: List[Dict[str, str]] = []
        
        # Guardrail keywords - questions must be finance-related
        self.finance_keywords = [
            'revenue', 'expense', 'profit', 'income', 'cost', 'payment', 'invoice',
            'cash', 'flow', 'receivable', 'payable', 'gst', 'tax', 'client',
            'budget', 'forecast', 'trend', 'financial', 'money', 'rupees', 'amount',
            'sales', 'purchase', 'bill', 'transaction', 'ledger', 'account',
            'margin', 'loss', 'gain', 'receivable', 'outstanding', 'paid', 'unpaid',
            'month', 'quarter', 'year', 'period', 'business', 'company',
            'hi', 'hello', 'hey', 'greetings', 'help', 'assist', 'test'
        ]
        
        # Blocked patterns - potential prompt injections
        self.blocked_patterns = [
            r'ignore\s+(previous|above|all)',
            r'forget\s+(everything|all|instructions)',
            r'new\s+instructions?',
            r'act\s+as',
            r'pretend\s+(to\s+be|you\s+are)',
            r'system\s+prompt',
            r'you\s+are\s+now',
            r'disregard',
            r'override',
            r'jailbreak',
            r'</?\s*system>',
            r'</?\s*prompt>',
            r'sudo\s+mode',
        ]
    
    def is_finance_related(self, question: str) -> bool:
        """
        Check if question is finance-related.
        
        Args:
            question: User question
            
        Returns:
            True if finance-related
        """
        question_lower = question.lower()
        
        # Check for finance keywords
        return any(keyword in question_lower for keyword in self.finance_keywords)
    
    def detect_prompt_injection(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect potential prompt injection attempts.
        
        Args:
            text: Input text to check
            
        Returns:
            (is_blocked, reason) tuple
        """
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True, f"Blocked pattern detected: {pattern}"
        
        # Check for excessive special characters (potential injection)
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / max(len(text), 1)
        if special_char_ratio > 0.3:
            return True, "Excessive special characters"
        
        # Check for very long input (potential overflow attack)
        if len(text) > 1000:
            return True, "Input too long"
        
        # Check for repeated tokens (potential token stuffing)
        words = text.lower().split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3 and len(words) > 10:
                return True, "Repetitive input pattern"
        
        return False, None
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input.
        
        Args:
            text: Raw input
            
        Returns:
            Sanitized text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML/XML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove control characters
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        
        return text.strip()
    
    def chat(self, user_question: str, financial_context: str) -> str:
        """
        Process user question with guardrails.
        
        Args:
            user_question: User's question
            financial_context: Current financial context
            
        Returns:
            AI response
        """
        # Sanitize input
        sanitized_question = self.sanitize_input(user_question)
        
        if not sanitized_question:
            return "Please provide a valid question."
        
        # GUARDRAILS DISABLED BY USER REQUEST
        # All queries will be passed directly to the AI model.
        
        # Check for prompt injection (Logging only, not blocking)
        is_blocked, reason = self.detect_prompt_injection(sanitized_question)
        if is_blocked:
            logger.warning(f"Potential injection pattern detected: {reason}")
            # Continuing anyway as per request
        
        # Check if finance-related (Logging only, not blocking)
        if not self.is_finance_related(sanitized_question):
             logger.info(f"Non-finance question detected: {sanitized_question}")
             # Continuing anyway as per request
        
        # Construct permissive prompt
        system_prompt = """You are Dinero AI, a helpful AI assistant.
        
        You have access to the user's financial data (provided in context below) but you can also answer general questions.
        
        GUIDELINES:
        1. If the user asks about their finances, use the provided FINANCIAL CONTEXT to answer accurately.
        2. Reference specific numbers from the context when discussing finances.
        3. If the user asks general questions (e.g., about cars, animals, world knowledge), answer them helpfully and naturally.
        4. Do NOT refuse to answer questions unless they are harmful or illegal.
        5. Keep responses concise and helpful.
        """
        
        user_prompt = f"""FINANCIAL CONTEXT:
{financial_context}

USER QUESTION:
{sanitized_question}

Provide a helpful answer."""
        
        try:
            # Call AI with secured prompt
            response = self.agent._call_with_retry(system_prompt + "\n\n" + user_prompt)
            response = self.agent._sanitize_output(response)
            
            # Additional output validation
            if len(response) > 500:
                response = response[:500] + "..."
            
            # Save to conversation history (limited to last 10)
            self.conversation_history.append({
                'question': sanitized_question,
                'answer': response
            })
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return response
            
        except AIAgentError as e:
            logger.error(f"Chatbot error: {str(e)}")
            return "I'm having trouble processing your question right now. Please try again."
        except Exception as e:
            logger.error(f"Unexpected chatbot error: {str(e)}")
            return "An error occurred. Please try rephrasing your question."
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get recent conversation history.
        
        Returns:
            List of conversation dictionaries with 'question' and 'answer' keys
        """
        return self.conversation_history
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
