"""
Test Purchase - Simulate a purchase to test PDF download and email delivery
"""
import sys
from database.models import Product, Order, get_session
from email_utils import send_order_confirmation_email, send_manual_ready_email
from pdf_manager import PDFManager
from google_drive_manager import GoogleDriveManager
from pathlib import Path

def test_purchase(product_id: int = 185871, customer_email: str = None):
    """
    Simulate a purchase and test the complete flow
    
    Args:
        product_id: Product ID to test
        customer_email: Email to send to (default: from .env)
    """
    if not customer_email:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        customer_email = os.getenv('FROM_EMAIL', 'test@example.com')
    
    print("="*70)
    print("🧪 SIMULATING PURCHASE")
    print("="*70)
    
    session = get_session()
    try:
        # Get product
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            print(f"❌ Product {product_id} not found!")
            return
        
        print(f"\n📦 Product: {product.title}")
        print(f"💰 Price: ${product.price}")
        print(f"📧 Customer: {customer_email}")
        print(f"🔗 PDF URL: {product.pdf_url[:50]}..." if product.pdf_url else "❌ No PDF URL")
        print()
        
        # Create test order
        order = Order(
            email=customer_email,
            product_id=product.id,
            price=product.price,
            paypal_order_id=f"TEST_{product_id}",
            status="completed"
        )
        session.add(order)
        session.commit()
        session.refresh(order)
        
        print(f"✅ Order #{order.id} created")
        print()
        
        # Send confirmation email
        print("📧 Sending confirmation email...")
        try:
            send_order_confirmation_email(
                to_email=customer_email,
                order_id=order.id,
                product_title=product.title,
                price=product.price
            )
            print("✅ Confirmation email sent")
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        print()
        print("-"*70)
        print("🚀 PROCESSING PDF DELIVERY")
        print("-"*70)
        print()
        
        # Check if Google Drive link exists
        google_drive_link = product.google_drive_link
        
        if not google_drive_link and product.pdf_url:
            print(f"📥 First purchase - downloading and uploading PDF...")
            print()
            
            # Download PDF
            pdf_manager = PDFManager()
            print("1️⃣ Downloading PDF...")
            pdf_result = pdf_manager.download_single_pdf(
                product_id=product.id,
                title=product.title,
                pdf_url=product.pdf_url
            )
            
            if pdf_result and pdf_result['success']:
                print(f"✅ PDF downloaded: {pdf_result['pdf_path']}")
                print()
                
                # Upload to Google Drive
                print("2️⃣ Uploading to Google Drive...")
                drive_manager = GoogleDriveManager()
                
                if drive_manager.service:
                    google_drive_link = drive_manager.upload_pdf(
                        file_path=Path(pdf_result['pdf_path']),
                        product_id=product.id,
                        title=product.title,
                        check_existing=False
                    )
                    
                    if google_drive_link:
                        # Save to database
                        product.google_drive_link = google_drive_link
                        product.pdf_processed = True
                        session.commit()
                        print(f"✅ Google Drive link: {google_drive_link[:60]}...")
                        print(f"✅ Link saved to database")
                    else:
                        print(f"❌ Upload failed")
                        google_drive_link = product.pdf_url
                else:
                    print(f"⚠️  Google Drive not configured")
                    google_drive_link = product.pdf_url
            else:
                print(f"❌ Download failed")
                google_drive_link = product.pdf_url
        else:
            print(f"✅ Using existing Google Drive link")
            print(f"   {google_drive_link[:60]}...")
        
        print()
        print("-"*70)
        print("📧 SENDING MANUAL LINK")
        print("-"*70)
        print()
        
        # Send manual link email
        if google_drive_link:
            try:
                send_manual_ready_email(
                    to_email=customer_email,
                    order_id=order.id,
                    product_title=product.title,
                    download_link=google_drive_link
                )
                print(f"✅ Manual link sent to {customer_email}")
            except Exception as e:
                print(f"❌ Failed to send email: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ No download link available")
        
        print()
        print("="*70)
        print("✅ TEST COMPLETE!")
        print("="*70)
        print()
        print("📧 Check your email for:")
        print("   1. Order confirmation")
        print("   2. Manual download link")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    # Get email from command line or use default
    email = sys.argv[1] if len(sys.argv) > 1 else None
    test_purchase(customer_email=email)
