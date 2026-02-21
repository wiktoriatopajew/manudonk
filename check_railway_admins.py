"""
Check admin users in Railway database directly
"""
import os
from database.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Railway PostgreSQL
DATABASE_URL = "postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("Checking admin users in Railway database...")
print("=" * 60)

admins = session.query(User).filter(User.is_admin == True).all()

if admins:
    print(f"\nAdmin users found: {len(admins)}")
    print("=" * 60)
    
    for admin in admins:
        print(f"\nEmail: {admin.email}")
        print(f"Is Admin: {admin.is_admin}")
        print(f"Is Verified: {admin.is_verified}")
        print(f"Created: {admin.created_at}")
        print("-" * 60)
    
    print("\n⚠️  UWAGA: Hasła są zaszyfrowane (bcrypt)!")
    print("Jeśli nie pamiętasz hasła, musisz je zresetować.")
else:
    print("\n❌ BRAK ADMINÓW W BAZIE!")
    print("\nUtwórz admina komendą:")
    print('python -c "import os; os.environ[\'DATABASE_URL\']=\'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway\'; from database.models import User, get_session; s = get_session(); u = User(email=\'admin@manualdonkey.com\', is_admin=True, is_verified=True); u.set_password(\'admin123\'); s.add(u); s.commit(); print(\'✓ Admin created!\')"')

all_users = session.query(User).all()
print(f"\nTotal users in database: {len(all_users)}")

session.close()
