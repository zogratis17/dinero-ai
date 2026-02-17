"""
Clean test of duplicate detection
"""
import pandas as pd
from datetime import datetime
import sys
import os
import uuid

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clean_test():
    """Run a clean test that matches existing database records."""
    from app import filter_duplicate_transactions, save_transactions_to_database, create_transaction_signature
    from database.connection import db_session
    from database.models import Business, JournalEntry
    
    default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    print("🧪 Clean Duplicate Detection Test\n")
    
    # First, see what's actually in the database
    with db_session() as session:
        existing_entries = session.query(JournalEntry).filter(
            JournalEntry.business_id == default_business_id
        ).all()
        
        print(f"📄 Current database entries: {len(existing_entries)}")
        if existing_entries:
            print("Existing transactions:")
            for i, entry in enumerate(existing_entries):
                # Get client info from first line
                client_name = ""
                amount = 0
                transaction_type = "expense"
                
                for line in entry.lines:
                    if line.client:
                        client_name = line.client.client_name
                    if line.debit_amount > 0 and line.account.account_type.value == "asset":
                        amount = line.debit_amount
                        transaction_type = "income"
                    elif line.debit_amount > 0:
                        amount = line.debit_amount
                        transaction_type = "expense"
                    
                print(f"  {i+1}. Date: {entry.entry_date}, Client: '{client_name}', Desc: '{entry.description}', Amount: {amount}, Type: {transaction_type}")
    
    # Now create a test transaction that matches one of the existing entries
    if existing_entries:
        first_entry = existing_entries[0]
        
        # Extract details from the first entry
        client_name = ""
        amount = 0
        transaction_type = "expense"
        
        for line in first_entry.lines:
            if line.client:
                client_name = line.client.client_name
            if line.debit_amount > 0 and line.account.account_type.value == "asset":
                amount = float(line.debit_amount)
                transaction_type = "income"
            elif line.debit_amount > 0:
                amount = float(line.debit_amount)
                transaction_type = "expense"
        
        # Create a matching transaction for duplicate detection
        matching_transaction = {
            'date': str(first_entry.entry_date),
            'client': client_name,
            'description': first_entry.description,
            'amount': amount,
            'type': transaction_type,
            'status': 'paid'
        }
        
        # Create a new (different) transaction
        new_transaction = {
            'date': '2026-01-25',
            'client': 'NewClient',
            'description': 'New Service',
            'amount': 2000,
            'type': 'income',
            'status': 'paid'
        }
        
        print(f"\n📊 Test data created:")
        print(f"Matching transaction: {matching_transaction}")
        print(f"New transaction: {new_transaction}")
        
        # Test duplicate detection
        test_data = pd.DataFrame([matching_transaction, new_transaction])
        
        print(f"\n🔍 Testing duplicate detection...")
        filtered_transactions, duplicate_count = filter_duplicate_transactions(test_data, default_business_id)
        
        print(f"\n📊 Results:")
        print(f"  - Input transactions: {len(test_data)}")
        print(f"  - Duplicates found: {duplicate_count}")
        print(f"  - New transactions: {len(filtered_transactions)}")
        
        if duplicate_count == 1 and len(filtered_transactions) == 1:
            print("✅ Duplicate detection working correctly!")
        else:
            print("❌ Duplicate detection not working as expected")
            
            # Debug signatures
            print("\n🔍 Debug signatures:")
            for idx, row in test_data.iterrows():
                sig = create_transaction_signature(row)
                print(f"  {idx}: {sig} - {row['client']} | {row['description']}")
    
    else:
        print("❌ No existing entries found in database")

if __name__ == "__main__":
    clean_test()