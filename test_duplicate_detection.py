"""
Test Duplicate Detection and Transaction Saving
This script tests the new duplicate detection functionality for CSV uploads.
"""
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_duplicate_detection():
    """Test the complete duplicate detection workflow."""
    print("🧪 Testing Duplicate Detection for CSV Uploads\n")
    
    from app import filter_duplicate_transactions, save_transactions_to_database, create_transaction_signature
    from config.settings import USE_DATABASE
    from database.connection import db_session
    from database.models import Business
    import uuid
    
    # Use the same default business_id as in app.py
    default_business_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    # Ensure the default business exists
    print(f"\n🏢 Ensuring default business exists...")
    with db_session() as session:
        business = session.query(Business).filter_by(id=default_business_id).first()
        if not business:
            business = Business(
                id=default_business_id,
                business_name="Test Business",
                currency_code='INR',
                is_active=True
            )
            session.add(business)
            session.commit()
            print("✅ Created default business")
        else:
            print("✅ Default business already exists")
    
    print(f"📋 Configuration:")
    print(f"   USE_DATABASE: {USE_DATABASE}")
    
    if not USE_DATABASE:
        print("❌ Database mode is disabled!")
        print("Please set USE_DATABASE=true in your .env file")
        return False
    
    # Create sample CSV data with some potential duplicates
    print("\n📊 Creating test CSV data...")
    
    base_date = datetime.now() - timedelta(days=30)
    test_data = []
    
    # Create base transactions
    base_transactions = [
        {'date': (base_date + timedelta(days=1)).strftime('%Y-%m-%d'), 'client': 'TechCorp', 'description': 'Web development project', 'amount': 15000, 'type': 'income', 'status': 'paid'},
        {'date': (base_date + timedelta(days=2)).strftime('%Y-%m-%d'), 'client': 'StartupX', 'description': 'Consulting services', 'amount': 8000, 'type': 'income', 'status': 'paid'},
        {'date': (base_date + timedelta(days=3)).strftime('%Y-%m-%d'), 'client': 'Office Supplies Ltd', 'description': 'Office supplies purchase', 'amount': 1200, 'type': 'expense', 'status': 'paid'},
        {'date': (base_date + timedelta(days=4)).strftime('%Y-%m-%d'), 'client': 'CloudHost Inc', 'description': 'Monthly hosting fee', 'amount': 500, 'type': 'expense', 'status': 'paid'},
    ]
    
    # Create new transactions (should be saved)
    new_transactions = [
        {'date': (base_date + timedelta(days=5)).strftime('%Y-%m-%d'), 'client': 'NewClient Corp', 'description': 'New project kickoff', 'amount': 25000, 'type': 'income', 'status': 'paid'},
        {'date': (base_date + timedelta(days=6)).strftime('%Y-%m-%d'), 'client': 'Another Client', 'description': 'Design services', 'amount': 12000, 'type': 'income', 'status': 'unpaid'},
    ]
    
    # Create duplicate transactions (should be filtered out)
    duplicate_transactions = [
        {'date': (base_date + timedelta(days=1)).strftime('%Y-%m-%d'), 'client': 'TechCorp', 'description': 'Web development project', 'amount': 15000, 'type': 'income', 'status': 'paid'},  # Exact duplicate
        {'date': (base_date + timedelta(days=2)).strftime('%Y-%m-%d'), 'client': 'StartupX', 'description': 'Consulting services', 'amount': 8000, 'type': 'income', 'status': 'paid'},  # Exact duplicate
    ]
    
    # Combine all transactions for the test
    test_data = base_transactions + new_transactions + duplicate_transactions
    
    print(f"✅ Created test dataset:")
    print(f"   - Base transactions: {len(base_transactions)}")
    print(f"   - New transactions: {len(new_transactions)}")  
    print(f"   - Duplicate transactions: {len(duplicate_transactions)}")
    print(f"   - Total in CSV: {len(test_data)}")
    
    # Convert to DataFrame (simulating CSV upload)
    df = pd.DataFrame(test_data)
    
    # First, save base transactions to simulate existing data
    print(f"\n💾 Saving base transactions to database...")
    base_saved = save_transactions_to_database(pd.DataFrame(base_transactions), default_business_id)
    print(f"✅ Saved {base_saved} base transactions")
    
    # Now test duplicate detection with the full dataset
    print(f"\n🔍 Testing duplicate detection...")
    filtered_transactions, duplicate_count = filter_duplicate_transactions(df, default_business_id)
    
    print(f"\n📊 Duplicate Detection Results:")
    print(f"   - Input transactions: {len(test_data)}")
    print(f"   - Duplicates found: {duplicate_count}")
    print(f"   - New transactions: {len(filtered_transactions)}")
    print(f"   - Expected new: {len(new_transactions)} (should match)")
    
    # Verify the results
    if duplicate_count == len(duplicate_transactions):
        print("✅ Duplicate detection working correctly!")
    else:
        print(f"❌ Expected {len(duplicate_transactions)} duplicates, found {duplicate_count}")
    
    if len(filtered_transactions) == len(new_transactions):
        print("✅ Correct number of new transactions identified!")
    else:
        print(f"❌ Expected {len(new_transactions)} new transactions, got {len(filtered_transactions)}")
    
    # Test saving the new transactions
    print(f"\n💾 Saving new transactions...")
    new_saved = save_transactions_to_database(filtered_transactions, default_business_id)
    print(f"✅ Saved {new_saved} new transactions")
    
    # Test signature creation
    print(f"\n🔑 Testing signature creation...")
    base_df = pd.DataFrame(base_transactions)
    duplicate_df = pd.DataFrame(duplicate_transactions)
    new_df = pd.DataFrame(new_transactions)
    
    sig1 = create_transaction_signature(base_df.iloc[0])
    sig2 = create_transaction_signature(duplicate_df.iloc[0])  # Should be same as first
    sig3 = create_transaction_signature(new_df.iloc[0])       # Should be different
    
    print(f"   - Base transaction signature: {sig1[:16]}...")
    print(f"   - Duplicate signature: {sig2[:16]}...")
    print(f"   - New transaction signature: {sig3[:16]}...")
    
    if sig1 == sig2:
        print("✅ Duplicate signature matching works!")
    else:
        print("❌ Duplicate signature matching failed!")
    
    if sig1 != sig3:
        print("✅ Different transactions have different signatures!")
    else:
        print("❌ Different transactions have same signature!")
    
    print(f"\n🎉 Duplicate detection test completed!")
    return True


def test_transaction_signatures():
    """Test various edge cases for transaction signature creation."""
    print("\n🔍 Testing Transaction Signature Edge Cases...")
    
    from app import create_transaction_signature
    
    # Test cases that should be considered the same
    similar_trans = [
        {'date': '2026-01-15', 'client': 'TechCorp', 'description': 'Software Development', 'amount': 1000, 'type': 'income'},
        {'date': '2026-01-15', 'client': 'TECHCORP', 'description': 'software development', 'amount': 1000.00, 'type': 'income'},  # Case differences
        {'date': '2026-01-15', 'client': 'TechCorp ', 'description': ' Software Development ', 'amount': 1000, 'type': 'income'},  # Extra spaces
    ]
    
    signatures = [create_transaction_signature(t) for t in similar_trans]
    
    print("Testing similar transactions:")
    for i, (trans, sig) in enumerate(zip(similar_trans, signatures)):
        print(f"   {i+1}: {sig[:12]}... - {trans['client']} | {trans['description']}")
    
    # All signatures should be the same
    if len(set(signatures)) == 1:
        print("✅ Similar transactions create identical signatures!")
    else:
        print("❌ Similar transactions create different signatures!")
        print(f"   Unique signatures: {len(set(signatures))}")
    
    # Test cases that should be different
    different_trans = [
        {'date': '2026-01-15', 'client': 'TechCorp', 'description': 'Software Development', 'amount': 1000, 'type': 'income'},
        {'date': '2026-01-15', 'client': 'TechCorp', 'description': 'Software Development', 'amount': 1500, 'type': 'income'},  # Different amount
        {'date': '2026-01-16', 'client': 'TechCorp', 'description': 'Software Development', 'amount': 1000, 'type': 'income'},  # Different date
        {'date': '2026-01-15', 'client': 'TechCorp', 'description': 'Web Development', 'amount': 1000, 'type': 'income'},      # Different description
    ]
    
    diff_signatures = [create_transaction_signature(t) for t in different_trans]
    
    print("\nTesting different transactions:")
    for i, (trans, sig) in enumerate(zip(different_trans, diff_signatures)):
        print(f"   {i+1}: {sig[:12]}... - {trans.get('amount', 'N/A')} | {trans.get('date', 'N/A')} | {trans.get('description', 'N/A')[:20]}")
    
    if len(set(diff_signatures)) == len(different_trans):
        print("✅ Different transactions create unique signatures!")
    else:
        print(f"❌ Some different transactions share signatures! Unique: {len(set(diff_signatures))}/{len(different_trans)}")


if __name__ == "__main__":
    print("Duplicate Detection Test Suite")
    print("=" * 50)
    
    # Run tests
    try:
        test_duplicate_detection()
        test_transaction_signatures()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()