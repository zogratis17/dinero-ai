"""
Debug signature generation differences
"""
import pandas as pd
from datetime import datetime
import sys
import os
import uuid
import hashlib

# Add the project root to Python path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_signatures():
    """Debug signature generation differences."""
    from database.connection import db_session
    from database.models import JournalEntry
    from decimal import Decimal
    
    default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    print("🔍 Debug Signature Generation\n")
    
    # Get first entry from database
    with db_session() as session:
        entry = session.query(JournalEntry).filter(
            JournalEntry.business_id == default_business_id
        ).first()
        
        if entry:
            # Extract details the same way the filter function does
            client_name = ""
            amount = Decimal('0.00')
            transaction_type = "expense"
            
            for line in entry.lines:
                if line.client:
                    client_name = line.client.client_name
                if line.debit_amount > 0:
                    amount = line.debit_amount
                    if line.account.account_type.value == "ASSET":  # Note: Enum value case
                        transaction_type = "income"
                elif line.credit_amount > 0:
                    amount = line.credit_amount
                    if line.account.account_type.value == "EXPENSE":
                        transaction_type = "expense"
            
            print(f"📄 Database entry details:")
            print(f"  Date: {entry.entry_date}")  
            print(f"  Client: '{client_name}'")
            print(f"  Description: '{entry.description}'")
            print(f"  Amount: {amount}")
            print(f"  Type: {transaction_type}")
            
            # Create signature the way the filter function does it
            client_normalized = client_name.lower().strip().replace(' ', '') if client_name else ''
            description_normalized = str(entry.description).lower().strip().replace(' ', '') if entry.description else ''
            amount_str = str(amount).strip()
            type_normalized = transaction_type.lower().strip()
            
            signature_data = f"{str(entry.entry_date)}|{client_normalized}|{description_normalized}|{amount_str}|{type_normalized}"
            db_signature = hashlib.md5(signature_data.encode()).hexdigest()
            
            print(f"\n🔑 Database signature creation:")
            print(f"  Signature data: '{signature_data}'")
            print(f"  Signature: {db_signature}")
            
            # Create matching CSV data
            csv_row = {
                'date': str(entry.entry_date),
                'client': client_name,
                'description': entry.description,
                'amount': float(amount),
                'type': transaction_type,
                'status': 'paid'
            }
            
            print(f"\n📊 CSV row data:")
            print(f"  {csv_row}")
            
            # Create signature the way create_transaction_signature does it
            from app import create_transaction_signature
            
            csv_df = pd.DataFrame([csv_row])
            csv_signature = create_transaction_signature(csv_df.iloc[0])
            
            print(f"\n🔑 CSV signature creation:")
            print(f"  Signature: {csv_signature}")
            
            print(f"\n📊 Comparison:")
            print(f"  Signatures match: {db_signature == csv_signature}")
            print(f"  DB signature:  {db_signature}")
            print(f"  CSV signature: {csv_signature}")

if __name__ == "__main__":
    debug_signatures()