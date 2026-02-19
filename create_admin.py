"""
Script to create or update admin user
Usage: python create_admin.py [email] [password]
"""

import sys
from database.models import get_session, User

def create_admin_user(email: str, password: str):
    """Create or update user as admin"""
    session = get_session()
    
    try:
        # Check if user exists
        user = session.query(User).filter(User.email == email).first()
        
        if user:
            print(f"User {email} already exists. Updating to admin...")
            user.is_admin = True
            user.is_verified = True
            user.set_password(password)
        else:
            print(f"Creating new admin user: {email}")
            user = User(
                email=email,
                is_admin=True,
                is_verified=True
            )
            user.set_password(password)
            session.add(user)
        
        session.commit()
        print(f"✓ Admin user created successfully!")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Admin: True")
        print(f"  Verified: True")
        print(f"\nYou can now login at http://localhost:8000/login")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
    
    # Add domain if not present
    if '@' not in email:
        email = f"{email}@example.com"
    
    create_admin_user(email, password)
