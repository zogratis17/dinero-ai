"""
Gmail Service - Send emails via Gmail API
Handles OAuth authentication and email sending functionality.
"""
import os
import base64
import logging
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")


class GmailServiceError(Exception):
    """Custom exception for Gmail service errors."""
    pass


def get_gmail_service():
    """
    Get authenticated Gmail API service.
    
    Returns:
        Gmail API service instance
        
    Raises:
        GmailServiceError: If credentials file is missing or authentication fails
        
    Note:
        Requires credentials.json file in the project root.
        Downloads from: https://console.cloud.google.com/apis/credentials
    """
    if not os.path.exists(CREDENTIALS_FILE):
        raise GmailServiceError(
            f"Gmail credentials file not found at {CREDENTIALS_FILE}. "
            "Please download OAuth 2.0 credentials from Google Cloud Console."
        )
    
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token file: {str(e)}")
            creds = None

    # Authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Gmail token refreshed successfully")
            except Exception as e:
                logger.error(f"Token refresh failed: {str(e)}")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Gmail authentication completed")
            except Exception as e:
                raise GmailServiceError(f"Gmail authentication failed: {str(e)}")

        # Save credentials for next run
        try:
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        except Exception as e:
            logger.warning(f"Failed to save token: {str(e)}")

    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise GmailServiceError(f"Failed to build Gmail service: {str(e)}")


def send_email(to_email: str, subject: str, html_body: str, from_name: Optional[str] = None) -> bool:
    """
    Send HTML email via Gmail API.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML content of the email
        from_name: Optional sender name (default: authenticated Gmail account)
        
    Returns:
        True if email was sent successfully
        
    Raises:
        GmailServiceError: If email sending fails
        ValueError: If parameters are invalid
        
    Example:
        >>> send_email(
        ...     "client@example.com",
        ...     "Payment Reminder",
        ...     "<h1>Hello</h1><p>This is a reminder...</p>"
        ... )
        True
    """
    # Validate inputs
    if not to_email or "@" not in to_email:
        raise ValueError("Invalid recipient email address")
    
    if not subject or not subject.strip():
        raise ValueError("Email subject cannot be empty")
    
    if not html_body or not html_body.strip():
        raise ValueError("Email body cannot be empty")
    
    try:
        service = get_gmail_service()

        # Create message
        message = MIMEText(html_body, "html")
        message["to"] = to_email
        message["subject"] = subject
        
        if from_name:
            message["from"] = from_name

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send email
        result = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()
        
        logger.info(f"Email sent successfully to {to_email}. Message ID: {result.get('id')}")
        return True
        
    except HttpError as e:
        logger.error(f"Gmail API error: {str(e)}")
        raise GmailServiceError(f"Failed to send email: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        raise GmailServiceError(f"Email sending failed: {str(e)}")


def is_gmail_configured() -> bool:
    """
    Check if Gmail service is properly configured.
    
    Returns:
        True if credentials file exists, False otherwise
    """
    return os.path.exists(CREDENTIALS_FILE)
