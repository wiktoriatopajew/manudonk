"""
Email tracking endpoints - for tracking opens and clicks
"""
import os
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from database.models import EmailTracking, AbandonedCart, Newsletter, get_session
from datetime import datetime
import json

tracking_router = APIRouter(prefix="/api/email", tags=["tracking"])

# Domain configuration
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")


@tracking_router.get("/track/{token}")
async def track_email_open(token: str):
    """Track email open via 1x1 transparent pixel"""
    session = get_session()
    
    try:
        tracking = session.query(EmailTracking).filter(
            EmailTracking.tracking_token == token
        ).first()
        
        if tracking and not tracking.opened:
            tracking.opened = True
            tracking.opened_at = datetime.utcnow()
            session.commit()
            print(f"📧 Email opened: {tracking.email}")
        
    except Exception as e:
        print(f"Tracking error: {e}")
    finally:
        session.close()
    
    # Return 1x1 transparent PNG
    transparent_pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    return Response(content=transparent_pixel, media_type="image/png")


@tracking_router.get("/click/{token}")
async def track_email_click(token: str, url: str = DOMAIN):
    """Track email click and redirect"""
    session = get_session()
    
    try:
        tracking = session.query(EmailTracking).filter(
            EmailTracking.tracking_token == token
        ).first()
        
        if tracking:
            if not tracking.clicked:
                tracking.clicked = True
                tracking.clicked_at = datetime.utcnow()
                print(f"🖱️ Email clicked: {tracking.email}")
            
            # Also mark as opened if not already
            if not tracking.opened:
                tracking.opened = True
                tracking.opened_at = datetime.utcnow()
            
            session.commit()
        
    except Exception as e:
        print(f"Click tracking error: {e}")
    finally:
        session.close()
    
    # Redirect to target URL
    return RedirectResponse(url=url, status_code=302)


class TrackCartRequest(BaseModel):
    email: str
    product_ids: list[int]
    total_value: float


@tracking_router.post("/track-cart")
async def track_abandoned_cart(data: TrackCartRequest):
    """Track cart for abandoned cart recovery"""
    session = get_session()
    
    try:
        # Check if cart already exists for this email
        existing_cart = session.query(AbandonedCart).filter(
            AbandonedCart.email == data.email,
            AbandonedCart.recovered == False
        ).first()
        
        if existing_cart:
            # Update existing cart
            existing_cart.product_ids = json.dumps(data.product_ids)
            existing_cart.total_value = data.total_value
            existing_cart.updated_at = datetime.utcnow()
            existing_cart.reminder_sent = False  # Reset reminder flag
            existing_cart.reminder_sent_at = None
        else:
            # Create new abandoned cart record
            cart = AbandonedCart(
                email=data.email,
                product_ids=json.dumps(data.product_ids),
                total_value=data.total_value
            )
            session.add(cart)
        
        session.commit()
        return {"success": True, "message": "Cart tracked"}
        
    except Exception as e:
        session.rollback()
        print(f"Error tracking cart: {e}")
        return {"success": False, "message": "Failed to track cart"}
    finally:
        session.close()


@tracking_router.post("/mark-purchased")
async def mark_newsletter_purchased(email: str):
    """Mark newsletter subscriber as having made a purchase"""
    session = get_session()
    
    try:
        # Mark newsletter subscriber as purchased
        subscriber = session.query(Newsletter).filter(
            Newsletter.email == email
        ).first()
        
        if subscriber:
            subscriber.has_purchased = True
            session.commit()
        
        # Mark abandoned carts as recovered
        carts = session.query(AbandonedCart).filter(
            AbandonedCart.email == email,
            AbandonedCart.recovered == False
        ).all()
        
        for cart in carts:
            cart.recovered = True
        
        session.commit()
        return {"success": True}
        
    except Exception as e:
        session.rollback()
        print(f"Error marking purchase: {e}")
        return {"success": False}
    finally:
        session.close()
