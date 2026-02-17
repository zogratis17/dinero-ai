"""
Debug the signature generation in filter_duplicate_transactions
"""
import pandas as pd
from datetime import datetime
import sys
import os
import uuid

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_signatures():
    """Debug signature generation for database records."""
    from app import create_transaction_signature
    from database.connection import db_session
    from database.models import Business, JournalEntry, AccountType
    import hashlib
    from decimal import Decimal
    
    default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    print("🔍 Debugging Signature Generation in Database\n")
    
    # Get existing entries and manually generate signatures
    with db_session() as session:
        existing_entries = session.query(JournalEntry).filter(
            JournalEntry.business_id == default_business_id
        ).all()
        
        print(f"📄 Processing {len(existing_entries)} database entries:\n")
        
        for i, entry in enumerate(existing_entries):
            print(f"Entry {i+1}:")
            print(f"  Date: {entry.entry_date}")
            print(f"  Description: '{entry.description}'")
            
            # Extract client and transaction details (same logic as in filter_duplicate_transactions)
            client_name = ""
            amount = Decimal('0.00')
            transaction_type = "expense"  # default
            
            for line in entry.lines:
                if line.client:
                    client_name = line.client.client_name
                if line.debit_amount > 0:
                    amount = line.debit_amount
                    if line.account.account_type == AccountType.INCOME:
                        transaction_type = "income"
                elif line.credit_amount > 0:
                    amount = line.credit_amount
                    if line.account.account_type == AccountType.EXPENSE:
                        transaction_type = "expense"
            
            print(f"  Extracted - Client: '{client_name}', Amount: {amount}, Type: {transaction_type}")
            
            # Generate signature using the same normalization logic as create_transaction_signature
            client_normalized = client_name.lower().strip().replace(' ', '') if client_name else ''
            description_normalized = str(entry.description).lower().strip().replace(' ', '') if entry.description else ''
            amount_str = str(amount).strip()
            type_normalized = transaction_type.lower().strip()
            
            signature_data = f"{str(entry.entry_date)}|{client_normalized}|{description_normalized}|{amount_str}|{type_normalized}"
            signature = hashlib.md5(signature_data.encode()).hexdigest()
            
            print(f"  Signature data: '{signature_data}'")
            print(f"  Signature: {signature}")
            print()
    
    # Now create a CSV-style record and generate its signature
    print("📊 CSV Test Record:")
    csv_record = {
        'date': '2026-01-19',
        'client': 'TechCorp',
        'description': 'Web development project',
        'amount': 15000.0,
        'type': 'income',
        'status': 'paid'
    }
    
    csv_df = pd.DataFrame([csv_record])
    csv_signature = create_transaction_signature(csv_df.iloc[0])
    
    print(f"CSV record: {csv_record}")
    print(f"CSV signature: {csv_signature}")
    
if __name__ == "__main__":
    debug_signatures()