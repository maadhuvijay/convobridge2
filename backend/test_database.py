"""
Test script to verify Supabase connection and session creation.
Run this to debug why sessions aren't appearing in Supabase.
"""

from database import (
    supabase, create_user, create_session, 
    get_user_by_name, get_active_session
)
from datetime import datetime

def test_database_connection():
    """Test if Supabase connection is working."""
    print("=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    
    if not supabase:
        print("❌ ERROR: Supabase client is not initialized!")
        print("   Check your .env file for SUPABASE_URL and SUPABASE_ANON_KEY")
        return False
    
    print("✓ Supabase client is initialized")
    
    # Test connection by querying users table
    try:
        response = supabase.table('users').select('count').execute()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_creation():
    """Test creating a user."""
    print("\n" + "=" * 60)
    print("Testing User Creation")
    print("=" * 60)
    
    test_username = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating test user: {test_username}")
    
    user = create_user(test_username)
    if user:
        print(f"✓ User created successfully: {user['id']}")
        return user
    else:
        print("❌ Failed to create user")
        return None

def test_session_creation(user_id: str):
    """Test creating a session."""
    print("\n" + "=" * 60)
    print("Testing Session Creation")
    print("=" * 60)
    
    print(f"Creating session for user: {user_id}")
    session = create_session(user_id)
    
    if session:
        print(f"✓ Session created successfully:")
        print(f"  - Session ID: {session['id']}")
        print(f"  - User ID: {session['user_id']}")
        print(f"  - Status: {session['status']}")
        print(f"  - Started at: {session.get('started_at', 'N/A')}")
        return session
    else:
        print("❌ Failed to create session")
        return None

def check_existing_sessions():
    """Check if there are any existing sessions in the database."""
    print("\n" + "=" * 60)
    print("Checking Existing Sessions")
    print("=" * 60)
    
    if not supabase:
        print("❌ Supabase not available")
        return
    
    try:
        # Check sessions table
        response = supabase.table('sessions').select('*').limit(10).execute()
        if response.data:
            print(f"✓ Found {len(response.data)} session(s) in database:")
            for session in response.data:
                print(f"  - Session {session['id']}: User {session['user_id']}, Status: {session['status']}")
        else:
            print("⚠ No sessions found in database")
        
        # Check users table
        users_response = supabase.table('users').select('*').limit(10).execute()
        if users_response.data:
            print(f"\n✓ Found {len(users_response.data)} user(s) in database:")
            for user in users_response.data:
                print(f"  - User {user['id']}: {user['name']}")
        else:
            print("\n⚠ No users found in database")
            
    except Exception as e:
        print(f"❌ Error checking sessions: {e}")
        print("\nThis might be due to Row Level Security (RLS) policies.")
        print("Check your Supabase dashboard -> Authentication -> Policies")

def check_rls_policies():
    """Provide guidance on RLS policies."""
    print("\n" + "=" * 60)
    print("RLS Policy Check")
    print("=" * 60)
    print("If you see 'No sessions found' but sessions should exist,")
    print("you may need to check Row Level Security policies in Supabase:")
    print("\n1. Go to Supabase Dashboard -> Table Editor -> sessions")
    print("2. Click on 'Policies' tab")
    print("3. Make sure there are policies that allow:")
    print("   - SELECT (to view data)")
    print("   - INSERT (to create sessions)")
    print("   - UPDATE (to update sessions)")
    print("\nFor development, you can temporarily disable RLS:")
    print("   ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;")
    print("\n(Remember to re-enable it for production!)")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ConvoBridge Database Test Script")
    print("=" * 60)
    
    # Test 1: Database connection
    if not test_database_connection():
        print("\n❌ Cannot proceed - database connection failed")
        print("Please check your .env file configuration")
        exit(1)
    
    # Test 2: Check existing data
    check_existing_sessions()
    
    # Test 3: Create test user and session
    user = test_user_creation()
    if user:
        session = test_session_creation(str(user['id']))
        if session:
            print("\n✓ All tests passed! Session should now be visible in Supabase.")
        else:
            print("\n❌ Session creation failed")
    else:
        print("\n❌ User creation failed - cannot test session creation")
    
    # Test 4: Check again after creation
    print("\n" + "=" * 60)
    print("Re-checking Sessions After Creation")
    print("=" * 60)
    check_existing_sessions()
    
    # RLS guidance
    check_rls_policies()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
