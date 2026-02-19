"""
List all users and their admin status
"""
from database.models import get_session, User

def list_users():
    session = get_session()
    try:
        users = session.query(User).all()
        
        if not users:
            print("No users found!")
            return
        
        print(f"Found {len(users)} users:")
        print("="*60)
        for user in users:
            print(f"Email: {user.email}")
            print(f"  is_admin: {user.is_admin}")
            print(f"  is_verified: {user.is_verified}")
            print(f"  created_at: {user.created_at}")
            print("-"*60)
        
    finally:
        session.close()

if __name__ == "__main__":
    list_users()
