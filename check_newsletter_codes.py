"""
Check newsletter discount codes in database
"""
from database.models import Newsletter, get_session

session = get_session()

try:
    newsletters = session.query(Newsletter).all()
    
    print(f"\n📧 Newsletter Subscribers: {len(newsletters)}")
    print("=" * 80)
    
    for nl in newsletters:
        status = "✅ ACTIVE" if nl.is_active else "❌ INACTIVE"
        purchased = "💰 PURCHASED" if nl.has_purchased else "🛒 NO PURCHASE"
        
        print(f"\nEmail: {nl.email}")
        print(f"Code: {nl.discount_code}")
        print(f"Status: {status}")
        print(f"Purchase: {purchased}")
        print(f"Subscribed: {nl.subscribed_at}")
        print("-" * 80)
    
    if newsletters:
        print(f"\n✨ Example code to test: {newsletters[0].discount_code}")
    else:
        print("\n⚠️  No newsletter subscribers found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
