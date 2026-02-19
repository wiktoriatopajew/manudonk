"""
Make wikitopajew@gmail.com an admin
"""
from database.models import get_session, User

def make_admin():
    session = get_session()
    try:
        user = session.query(User).filter(User.email == "wikitopajew@gmail.com").first()
        
        if not user:
            print("❌ User not found!")
            return
        
        if user.is_admin:
            print(f"✅ {user.email} is already an admin")
        else:
            user.is_admin = True
            session.commit()
            print(f"✅ {user.email} is now an admin!")
        
        print(f"   is_admin: {user.is_admin}")
        print(f"   is_verified: {user.is_verified}")
        
    finally:
        session.close()

if __name__ == "__main__":
    make_admin()
