"""
Background tasks for email automation
Run this script periodically (e.g., via cron or Windows Task Scheduler)
"""
from database.models import get_session, Newsletter, AbandonedCart, Product
from email_utils import send_abandoned_cart_email, send_discount_reminder_email
from datetime import datetime, timedelta
import json


def send_abandoned_cart_reminders():
    """Send reminder emails for abandoned carts after 24 hours"""
    session = get_session()
    
    try:
        # Find carts abandoned more than 24 hours ago that haven't received reminders
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        abandoned_carts = session.query(AbandonedCart).filter(
            AbandonedCart.created_at < cutoff_time,
            AbandonedCart.reminder_sent == False,
            AbandonedCart.recovered == False
        ).all()
        
        print(f"🛒 Found {len(abandoned_carts)} abandoned carts to process")
        
        for cart in abandoned_carts:
            try:
                # Get product details
                product_ids = json.loads(cart.product_ids)
                products = []
                
                for product_id in product_ids:
                    product = session.query(Product).filter(Product.id == product_id).first()
                    if product:
                        products.append({
                            'title': product.title,
                            'price': product.price
                        })
                
                if products:
                    # Send reminder email
                    result = send_abandoned_cart_email(
                        cart.email,
                        products,
                        cart.total_value
                    )
                    
                    if result:
                        # Mark as sent
                        cart.reminder_sent = True
                        cart.reminder_sent_at = datetime.utcnow()
                        session.commit()
                        print(f"✅ Sent abandoned cart reminder to {cart.email}")
                    else:
                        print(f"⚠️ Failed to send reminder to {cart.email}")
                        
            except Exception as e:
                print(f"❌ Error processing cart {cart.id}: {e}")
                continue
        
        print(f"✅ Abandoned cart reminders completed")
        
    except Exception as e:
        print(f"Error in abandoned cart reminders: {e}")
    finally:
        session.close()


def send_discount_code_reminders():
    """Send reminder about discount code 7 days after subscription if not purchased"""
    session = get_session()
    
    try:
        # Find subscribers who subscribed 7 days ago, haven't purchased, and haven't received reminder
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        subscribers = session.query(Newsletter).filter(
            Newsletter.subscribed_at < cutoff_time,
            Newsletter.has_purchased == False,
            Newsletter.is_active == True,
            Newsletter.last_reminder_sent.is_(None)
        ).all()
        
        print(f"📧 Found {len(subscribers)} subscribers to remind about discount code")
        
        for subscriber in subscribers:
            try:
                # Send reminder
                result = send_discount_reminder_email(
                    subscriber.email,
                    subscriber.discount_code
                )
                
                if result:
                    # Mark reminder as sent
                    subscriber.last_reminder_sent = datetime.utcnow()
                    session.commit()
                    print(f"✅ Sent discount reminder to {subscriber.email}")
                else:
                    print(f"⚠️ Failed to send reminder to {subscriber.email}")
                    
            except Exception as e:
                print(f"❌ Error processing subscriber {subscriber.id}: {e}")
                continue
        
        print(f"✅ Discount reminders completed")
        
    except Exception as e:
        print(f"Error in discount reminders: {e}")
    finally:
        session.close()


def mark_newsletters_as_purchased(email: str):
    """Mark newsletter subscriber as having made a purchase"""
    session = get_session()
    
    try:
        subscriber = session.query(Newsletter).filter(
            Newsletter.email == email
        ).first()
        
        if subscriber and not subscriber.has_purchased:
            subscriber.has_purchased = True
            session.commit()
            print(f"✅ Marked {email} as purchased in newsletter")
            
    except Exception as e:
        print(f"Error marking purchase: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Starting email automation tasks...")
    print("=" * 50)
    
    # Run abandoned cart reminders
    send_abandoned_cart_reminders()
    print()
    
    # Run discount code reminders
    send_discount_code_reminders()
    print()
    
    print("=" * 50)
    print("✅ Email automation completed!")
