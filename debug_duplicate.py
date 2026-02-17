"""
Simple duplicate detection debug test
"""
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import uuid

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_duplicate_detection():
    """Debug the duplicate detection step by step."""
    from app import filter_duplicate_transactions, create_transaction_signature
    from database.connection import db_session
    from database.models import Business, JournalEntry
    
    default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    print("🔍 Debugging Duplicate Detection Logic\n")
    
    # Create very simple test data
    base_transaction = {
        'date': '2026-01-15',
        'client': 'TechCorp',
        'description': 'Software Development',
        'amount': 1000,
        'type': 'income',
        'status': 'paid'
    }
    
    duplicate_transaction = {
        'date': '2026-01-15',
        'client': 'TechCorp',
        'description': 'Software Development',
        'amount': 1000,
        'type': 'income',
        'status': 'paid'
    }
    
    print("📊 Test Data:")
    print(f"Base: {base_transaction}")
    print(f"Duplicate: {duplicate_transaction}")
    
    # Create signatures
    base_df = pd.DataFrame([base_transaction])
    duplicate_df = pd.DataFrame([duplicate_transaction])
    
    base_sig = create_transaction_signature(base_df.iloc[0])
    dup_sig = create_transaction_signature(duplicate_df.iloc[0])
    
    print(f"\n🔑 Signatures:")
    print(f"Base signature: {base_sig}")
    print(f"Duplicate signature: {dup_sig}")
    print(f"Signatures match: {base_sig == dup_sig}")
    
    # Check what's in the database
    with db_session() as session:
        existing_entries = session.query(JournalEntry).filter(
            JournalEntry.business_id == default_business_id
        ).all()
        
        print(f"\n📄 Existing entries in database: {len(existing_entries)}")
        for i, entry in enumerate(existing_entries[:5]):  # Show first 5
            print(f"  {i+1}. Date: {entry.entry_date}, Desc: {entry.description}")
    
    # Test the filter function
    test_data = pd.DataFrame([duplicate_transaction])
    
    print(f"\n🧪 Testing filter_duplicate_transactions...")
    print(f"Input DataFrame shape: {test_data.shape}")
    
    filtered_transactions, duplicate_count = filter_duplicate_transactions(test_data, default_business_id)
    
    print(f"Result: {duplicate_count} duplicates, {len(filtered_transactions)} new")
    
    # Debug the signature creation in filter function
    print(f"\n🔍 Signature creation in CSV data:")
    test_data['debug_signature'] = test_data.apply(create_transaction_signature, axis=1)
    print(f"CSV signature: {test_data['debug_signature'].iloc[0]}")
    

if __name__ == "__main__":
    debug_duplicate_detection()