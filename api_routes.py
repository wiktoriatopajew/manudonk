"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
from database.models import User, VerificationCode, Order, Product, PasswordResetToken, Newsletter, DiscountCode, get_session
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload
from auth import create_access_token, get_current_user, get_current_admin_user
from email_utils import send_verification_email, send_order_confirmation_email, send_manual_ready_email, send_password_reset_email, send_welcome_newsletter_email, send_admin_order_notification
import stripe
import os
import secrets
import string
from dotenv import load_dotenv

# Load environment variables
# Note: load_dotenv() with override=False (default) will NOT override existing env vars
# This means Railway variables should take precedence
load_dotenv(override=False)

# Debug: Check if .env file exists
env_file_exists = os.path.exists(".env")
print(f"🔍 .env file exists: {env_file_exists}")

# Stripe configuration
# Try multiple variations in case Railway added newlines or spaces
stripe_key = None
for key_name in ["STRIPE_SECRET_KEY", "STRIPE_SECRET_KEY\n", "STRIPE_SECRET_KEY "]:
    stripe_key = os.getenv(key_name)
    if stripe_key:
        stripe_key = stripe_key.strip()  # Remove any whitespace/newlines
        print(f"🔍 Found Stripe key with name: '{key_name}'")
        break

# If not found, try searching all env vars
if not stripe_key:
    for key, value in os.environ.items():
        if 'STRIPE_SECRET_KEY' in key:
            stripe_key = value.strip()
            print(f"🔍 Found Stripe key in env var: '{key}' (cleaned)")
            break

print(f"🔍 Raw STRIPE_SECRET_KEY from environment: {stripe_key[:30] if stripe_key else 'NOT SET'}...")

if stripe_key and stripe_key != "sk_test_placeholder":
    stripe.api_key = stripe_key
    print(f"✅ Stripe configured with key: {stripe_key[:15]}...")
    print(f"   Key length: {len(stripe_key)} characters")
else:
    print("⚠️  WARNING: STRIPE_SECRET_KEY not found! Payments will not work.")
    print(f"⚠️  Available env vars starting with STRIPE: {[k for k in os.environ.keys() if 'STRIPE' in k.upper()]}")
    stripe.api_key = "sk_test_placeholder"  # Prevent crash
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_your_webhook_secret_here")

# Domain configuration - auto-detect Railway or use .env
railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
railway_static_url = os.getenv("RAILWAY_STATIC_URL")
if railway_domain:
    DOMAIN = f"https://{railway_domain}"
    print(f"✅ Using Railway domain: {DOMAIN}")
elif railway_static_url:
    DOMAIN = railway_static_url
    print(f"✅ Using Railway static URL: {DOMAIN}")
else:
    DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")
    print(f"⚠️  Using fallback domain: {DOMAIN}")

router = APIRouter(prefix="/api/auth", tags=["auth"])
orders_router = APIRouter(prefix="/api/orders", tags=["orders"])
import_router = APIRouter(prefix="/api/import", tags=["import"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    marketing_consent: bool = False


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class ResendCodeRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register")
async def register(request: RegisterRequest):
    """Register new user"""
    session = get_session()
    try:
        # Check if user exists
        existing_user = session.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user = User(email=request.email, marketing_consent=request.marketing_consent)
        user.set_password(request.password)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Generate verification code
        code = VerificationCode.generate_code()
        verification = VerificationCode(
            user_id=user.id,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        session.add(verification)
        session.commit()
        
        # Try to send verification email
        try:
            send_verification_email(user.email, code)
            message = "Registration successful. Please check your email for verification code."
        except Exception as e:
            print(f"Error sending verification email: {e}")
            # Don't auto-verify - user needs to verify via email
            message = "Registration successful. Please check your email for verification code."
        
        return {"message": message}
    finally:
        session.close()


@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """Verify email with code"""
    session = get_session()
    try:
        user = session.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")
        
        # Find valid verification code
        verification = session.query(VerificationCode).filter(
            VerificationCode.user_id == user.id,
            VerificationCode.code == request.code,
            VerificationCode.used == False
        ).order_by(VerificationCode.created_at.desc()).first()
        
        if not verification:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        
        if not verification.is_valid():
            raise HTTPException(status_code=400, detail="Verification code expired")
        
        # Mark as verified
        user.is_verified = True
        verification.used = True
        session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "message": "Email verified successfully",
            "access_token": access_token,
            "token_type": "bearer"
        }
    finally:
        session.close()


@router.post("/resend-code")
async def resend_verification_code(request: ResendCodeRequest):
    """Resend verification code"""
    session = get_session()
    try:
        user = session.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")
        
        # Generate new code
        code = VerificationCode.generate_code()
        verification = VerificationCode(
            user_id=user.id,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        session.add(verification)
        session.commit()
        
        # Send email
        send_verification_email(user.email, code)
        
        return {"message": "Verification code sent"}
    finally:
        session.close()


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset"""
    session = get_session()
    try:
        user = session.query(User).filter(User.email == request.email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return {"message": "If the email exists, a reset link will be sent"}
        
        # Generate reset token
        token = PasswordResetToken.generate_token()
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        session.add(reset_token)
        session.commit()
        
        # Send email
        domain = os.getenv("DOMAIN", "http://localhost:8000")
        send_password_reset_email(user.email, token, domain)
        
        return {"message": "If the email exists, a reset link will be sent"}
    finally:
        session.close()


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token"""
    session = get_session()
    try:
        # Find valid token
        reset_token = session.query(PasswordResetToken).filter(
            PasswordResetToken.token == request.token
        ).first()
        
        if not reset_token or not reset_token.is_valid():
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Update password
        user = session.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.set_password(request.new_password)
        reset_token.used = True
        session.commit()
        
        return {"message": "Password reset successfully"}
    finally:
        session.close()


@router.post("/create-account-after-purchase")
async def create_account_after_purchase(request: RegisterRequest):
    """Create account after successful purchase - no email verification needed"""
    session = get_session()
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account with this email already exists. Please login."
            )
        
        # Create new user with verified status
        user = User(
            email=request.email,
            is_verified=True  # Auto-verified since they paid
        )
        user.set_password(request.password)
        session.add(user)
        session.commit()
        
        # Link existing orders to this user
        orders = session.query(Order).filter(Order.email == request.email).all()
        for order in orders:
            order.user_id = user.id
        session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "message": "Account created successfully",
            "access_token": access_token,
            "token_type": "bearer"
        }
    finally:
        session.close()


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user"""
    session = get_session()
    try:
        user = session.query(User).filter(User.email == form_data.username).first()
        if not user or not user.verify_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your email."
            )
        
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "is_admin": user.is_admin
        }
    finally:
        session.close()


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at
    }


@router.get("/my-orders")
async def get_my_orders(current_user: User = Depends(get_current_user)):
    """Get orders for current logged in user"""
    session = get_session()
    try:
        # Get orders by user_id OR by email (for orders placed before account creation)
        orders = session.query(Order).filter(
            (Order.user_id == current_user.id) | (Order.email == current_user.email)
        ).order_by(Order.created_at.desc()).all()
        
        return [
            {
                "id": order.id,
                "product_title": order.product.title,
                "product_brand": order.product.brand,
                "product_model": order.product.model,
                "price": order.price,
                "status": order.status,
                "download_link": order.download_link,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            for order in orders
        ]
    finally:
        session.close()


@router.post("/admin/fix-verification")
async def fix_user_verification():
    """TEMPORARY: Fix all users by setting is_verified=True"""
    session = get_session()
    try:
        # Get unverified users
        unverified_users = session.query(User).filter(User.is_verified == False).all()
        
        if not unverified_users:
            return {
                "message": "All users are already verified",
                "fixed_count": 0
            }
        
        # Fix them
        for user in unverified_users:
            user.is_verified = True
        
        session.commit()
        
        return {
            "message": f"Fixed {len(unverified_users)} users",
            "fixed_count": len(unverified_users),
            "fixed_emails": [u.email for u in unverified_users]
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/admin/list-users-simple")
async def list_users_simple():
    """TEMPORARY: Simple user list from Railway Postgres"""
    session = get_session()
    try:
        users = session.query(User).all()
        
        return {
            "total": len(users),
            "admins": [
                {
                    "email": u.email,
                    "is_admin": u.is_admin,
                    "is_verified": u.is_verified,
                    "created": str(u.created_at) if u.created_at else None
                }
                for u in users if u.is_admin
            ],
            "regular_users": [
                {
                    "email": u.email,
                    "is_verified": u.is_verified,
                    "created": str(u.created_at) if u.created_at else None
                }
                for u in users if not u.is_admin
            ]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()


@router.get("/admin/diagnose-users")
async def diagnose_all_users():
    """TEMPORARY: Show all users with details for diagnosis"""
    session = get_session()
    try:
        users = session.query(User).all()
        
        result = {
            "total_users": len(users),
            "users": []
        }
        
        for user in users:
            result["users"].append({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "password_hash_length": len(user.password_hash) if user.password_hash else 0,
                "password_hash_starts_with": user.password_hash[:10] if user.password_hash else "NO HASH",
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


class CreateAdminRequest(BaseModel):
    email: EmailStr
    password: str
    secret_key: str  # Simple security


@router.post("/admin/create-admin-account")
async def create_admin_account(request: CreateAdminRequest):
    """TEMPORARY: Create admin account with secret key"""
    # Simple security check
    if request.secret_key != "manualbear2026":
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    session = get_session()
    try:
        # Check if user exists
        user = session.query(User).filter(User.email == request.email).first()
        
        if user:
            # Update existing user to admin
            user.is_admin = True
            user.is_verified = True
            user.set_password(request.password)
            session.commit()
            
            return {
                "message": "User updated to admin",
                "email": user.email,
                "is_admin": user.is_admin
            }
        else:
            # Create new admin
            new_admin = User(
                email=request.email,
                is_admin=True,
                is_verified=True
            )
            new_admin.set_password(request.password)
            session.add(new_admin)
            session.commit()
            
            return {
                "message": "Admin user created",
                "email": new_admin.email,
                "is_admin": new_admin.is_admin
            }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/admin/users")
async def get_all_users(page: int = 1, per_page: int = 10, current_user: User = Depends(get_current_admin_user)):
    """Get all users with pagination (admin only)"""
    session = get_session()
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        total_count = session.query(User).count()
        
        # Get users for current page
        users = session.query(User).order_by(desc(User.created_at))\
            .offset(offset)\
            .limit(per_page)\
            .all()
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
    finally:
        session.close()


@router.get("/admin/orders")
async def get_all_orders(
    page: int = 1, 
    per_page: int = 10, 
    current_user: User = Depends(get_current_admin_user)
):
    """Get all orders with pagination (admin only)"""
    session = get_session()
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count and revenue
        total_count = session.query(Order).count()
        total_revenue = session.query(func.sum(Order.price)).scalar() or 0.0
        
        # Get orders for current page with product information
        orders = session.query(Order).options(joinedload(Order.product))\
            .order_by(desc(Order.created_at))\
            .offset(offset)\
            .limit(per_page)\
            .all()
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "orders": [
                {
                    "id": order.id,
                    "email": order.email,
                    "product_id": order.product_id,
                    "product_title": order.product.title if order.product else None,
                    "price": order.price,
                    "status": order.status,
                    "download_link": order.download_link,
                    "paypal_order_id": order.paypal_order_id,
                    "created_at": order.created_at
                }
                for order in orders
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "total_revenue": total_revenue
            }
        }
    finally:
        session.close()


class UpdateOrderRequest(BaseModel):
    download_link: str


@router.put("/admin/orders/{order_id}")
async def update_order(order_id: int, request: UpdateOrderRequest, current_user: User = Depends(get_current_admin_user)):
    """Update order download link (admin only)"""
    session = get_session()
    try:
        order = session.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get product info for email
        product = session.query(Product).filter(Product.id == order.product_id).first()
        
        order.download_link = request.download_link
        session.commit()
        
        # Send notification email to customer
        if order.email and product:
            send_manual_ready_email(
                order.email,
                order.id,
                product.title,
                request.download_link
            )
        
        return {"message": "Order updated successfully"}
    finally:
        session.close()



# Search Autocomplete API
search_router = APIRouter(prefix="/api/search", tags=["search"])


@search_router.get("/autocomplete")
async def search_autocomplete(q: str):
    """Get search suggestions for autocomplete"""
    if not q or len(q) < 2:
        return {"suggestions": []}
    
    session = get_session()
    try:
        # Search in brands, models, categories, and titles
        from sqlalchemy import or_, func, and_
        import re
        
        # Check if user specified a year in search query (e.g., "Focus 2009")
        year_in_query = None
        year_match = re.search(r'\b(19|20)\d{2}\b', q)
        if year_match:
            year_in_query = int(year_match.group(0))
        
        # Normalize search query: remove special chars, extra spaces
        # "f-150" -> "f150", "F 150" -> "f150"
        normalized_q = re.sub(r'[^\w\s]', '', q.lower())  # Remove special chars
        normalized_q = re.sub(r'\s+', ' ', normalized_q).strip()  # Normalize spaces
        
        # Split search term into words for better matching
        search_words = normalized_q.split()
        
        # Remove year from search words if found (we'll handle it separately)
        if year_in_query:
            search_words = [w for w in search_words if w != str(year_in_query)]
        
        # Create filters for each word
        word_filters = []
        # Check database type for regexp support
        from database.models import DATABASE_URL
        use_regexp = not DATABASE_URL.startswith("sqlite")
        
        for word in search_words:
            if len(word) >= 2:  # Only search words with 2+ characters
                search_term = f"%{word}%"
                # Search in normalized fields (without special chars)
                if use_regexp:
                    # PostgreSQL: use regexp_replace to normalize
                    word_filters.append(
                        or_(
                            func.regexp_replace(func.lower(Product.brand), '[^a-z0-9 ]', '', 'g').like(search_term),
                            func.regexp_replace(func.lower(Product.model), '[^a-z0-9 ]', '', 'g').like(search_term),
                            func.regexp_replace(func.lower(Product.category), '[^a-z0-9 ]', '', 'g').like(search_term),
                            func.regexp_replace(func.lower(Product.title), '[^a-z0-9 ]', '', 'g').like(search_term)
                        )
                    )
                else:
                    # SQLite: use simple LIKE (search term already normalized in Python)
                    word_filters.append(
                        or_(
                            func.lower(Product.brand).like(search_term),
                            func.lower(Product.model).like(search_term),
                            func.lower(Product.category).like(search_term),
                            func.lower(Product.title).like(search_term)
                        )
                    )
        
        # Get products matching all words
        if word_filters:
            products = session.query(Product).filter(and_(*word_filters)).limit(20).all()
        else:
            products = []
        
        # Filter by year range if year was specified in search
        if year_in_query:
            filtered_products = []
            for product in products:
                # Check if title contains a year range like "2005-2010"
                range_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', product.title)
                if range_match:
                    year_start = int(range_match.group(1))
                    year_end = int(range_match.group(2))
                    # Include if searched year is within range
                    if year_start <= year_in_query <= year_end:
                        filtered_products.append(product)
                # Also include if product.year matches
                elif product.year and product.year == year_in_query:
                    filtered_products.append(product)
                # Or if title contains the exact year
                elif str(year_in_query) in product.title:
                    filtered_products.append(product)
            
            products = filtered_products[:4]
        else:
            products = products[:4]
        
        suggestions = []
        seen = set()
        
        for product in products:
            # Add product suggestion
            if product.title.lower() not in seen:
                suggestions.append({
                    "text": product.title,
                    "type": "product",
                    "url": f"/manuals/{product.slug}" if product.slug else f"/product/{product.id}"
                })
                seen.add(product.title.lower())
            
            if len(suggestions) >= 4:
                break
        
        return {"suggestions": suggestions[:4]}
    finally:
        session.close()


# Orders API
class CreateCheckoutSessionRequest(BaseModel):
    product_id: int
    discount_code: Optional[str] = None

class CreateMultiCheckoutSessionRequest(BaseModel):
    product_ids: List[int]
    discount_code: Optional[str] = None


@orders_router.get("/session-email")
async def get_session_email(session_id: str):
    """Get customer email from Stripe session, create order if needed, and auto-login if user exists"""
    db_session = get_session()
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        email = checkout_session.customer_details.email if checkout_session.customer_details else None
        
        if not email:
            return {"email": None, "access_token": None}
        
        # Get payment intent ID
        payment_intent = checkout_session.payment_intent
        
        # NOTE: Orders are created by webhook (checkout.session.completed event)
        # This endpoint only retrieves email and checks user status for auto-login
        # No order creation here to avoid race conditions and duplicates
        
        print(f"📧 Success page accessed for payment_intent: {payment_intent}")
        
        # Check if user exists and is verified
        user = db_session.query(User).filter(User.email == email).first()
        
        # Get order details for conversion tracking
        # For multi-product orders, sum up all orders with this payment_intent
        all_orders = db_session.query(Order).filter(Order.paypal_order_id == payment_intent).all()
        
        if all_orders:
            order_id = all_orders[0].id if len(all_orders) == 1 else f"MULTI-{payment_intent[:8]}"
            order_total = sum(order.price for order in all_orders)
            print(f"✅ Found {len(all_orders)} order(s) for this payment, total: ${order_total}")
        else:
            order_id = None
            order_total = None
            print(f"⚠️  No orders found yet for payment_intent {payment_intent} - webhook may still be processing")
        
        if user and user.is_verified:
            # Generate access token for automatic login
            access_token = create_access_token(data={"sub": user.email})
            return {
                "email": email,
                "access_token": access_token,
                "user_exists": True,
                "order_id": order_id,
                "order_total": float(order_total) if order_total else None
            }
        
        return {
            "email": email,
            "access_token": None,
            "user_exists": False,
            "order_id": order_id,
            "order_total": float(order_total) if order_total else None
        }
    except Exception as e:
        print(f"Error in session-email: {e}")
        import traceback
        traceback.print_exc()
        return {"email": None, "access_token": None}
    finally:
        db_session.close()


@orders_router.get("/config-check")
async def check_configuration():
    """Check if payment system is properly configured"""
    return {
        "stripe_configured": bool(stripe.api_key and stripe.api_key != "sk_test_placeholder"),
        "stripe_key_prefix": stripe.api_key[:15] if stripe.api_key else "NOT SET",
        "stripe_key_length": len(stripe.api_key) if stripe.api_key else 0,
        "domain": DOMAIN,
        "webhook_secret_set": bool(STRIPE_WEBHOOK_SECRET and STRIPE_WEBHOOK_SECRET != "whsec_your_webhook_secret_here")
    }


@orders_router.get("/debug")
async def debug_configuration():
    """Detailed debug information about configuration"""
    import os
    return {
        "stripe": {
            "api_key_set": bool(stripe.api_key),
            "api_key_prefix": stripe.api_key[:20] if stripe.api_key else "NOT SET",
            "api_key_length": len(stripe.api_key) if stripe.api_key else 0,
            "is_test_key": stripe.api_key.startswith("sk_test_") if stripe.api_key else False,
            "is_live_key": stripe.api_key.startswith("sk_live_") if stripe.api_key else False,
            "is_placeholder": stripe.api_key == "sk_test_placeholder" if stripe.api_key else True
        },
        "domain": {
            "current": DOMAIN,
            "railway_public_domain": os.getenv("RAILWAY_PUBLIC_DOMAIN"),
            "railway_static_url": os.getenv("RAILWAY_STATIC_URL"),
            "env_domain": os.getenv("DOMAIN")
        },
        "webhook": {
            "secret_set": bool(STRIPE_WEBHOOK_SECRET),
            "is_placeholder": STRIPE_WEBHOOK_SECRET == "whsec_your_webhook_secret_here"
        },
        "environment": {
            "has_env_file": os.path.exists(".env"),
            "stripe_secret_key_env": "SET" if os.getenv("STRIPE_SECRET_KEY") else "NOT SET",
            "all_env_vars_with_stripe": [k for k in os.environ.keys() if 'STRIPE' in k.upper()],
            "all_env_vars_count": len(os.environ.keys()),
            "railway_vars": [k for k in os.environ.keys() if k.startswith('RAILWAY_')]
        }
    }


@orders_router.post("/create-checkout-session")
async def create_checkout_session(request: CreateCheckoutSessionRequest):
    """Create Stripe checkout session"""
    session = get_session()
    try:
        print(f"💳 Single checkout request: product_id={request.product_id}, discount='{request.discount_code}'")
        print(f"🔑 Stripe API Key status: {'SET' if stripe.api_key else 'NOT SET'}")
        print(f"🔑 Stripe API Key prefix: {stripe.api_key[:20] if stripe.api_key else 'N/A'}")
        print(f"🔑 Is placeholder: {stripe.api_key == 'sk_test_placeholder'}")
        
        # Validate Stripe is configured
        if not stripe.api_key or stripe.api_key == "sk_test_placeholder":
            error_msg = f"Payment system not configured. Stripe key: {stripe.api_key[:30] if stripe.api_key else 'NOT SET'}"
            print(f"❌ {error_msg}")
            raise HTTPException(
                status_code=500, 
                detail=error_msg
            )
        
        # Get product
        product = session.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Validate product has a price
        if not product.price or product.price <= 0:
            raise HTTPException(
                status_code=500,
                detail=f"Product {product.id} has invalid price: {product.price}"
            )
        
        # Calculate price with discount if provided
        final_price = product.price
        discount_amount = 0
        metadata = {'product_id': product.id}
        
        # Validate discount code if provided
        if request.discount_code:
            # Clean and normalize the code
            clean_code = request.discount_code.strip().upper()
            print(f"🎫 Validating discount code: '{clean_code}'")
            
            # First check regular discount codes
            discount = session.query(DiscountCode).filter(
                DiscountCode.code == clean_code
            ).first()
            
            if discount:
                print(f"✅ Found regular discount code: {discount.code}")
                valid, message = discount.is_valid()
                if valid:
                    discount_amount = discount.calculate_discount(product.price)
                    final_price = max(0.50, product.price - discount_amount)  # Minimum $0.50 for Stripe
                    metadata['discount_code'] = discount.code
                    metadata['discount_amount'] = str(discount_amount)
                    metadata['original_price'] = str(product.price)
            else:
                # Check newsletter discount codes (10% off)
                newsletter = session.query(Newsletter).filter(
                    Newsletter.discount_code == clean_code,
                    Newsletter.is_active == True
                ).first()
                
                if newsletter:
                    print(f"✅ Found newsletter discount code: {newsletter.discount_code}")
                    discount_amount = product.price * 0.10  # 10% off
                    final_price = max(0.50, product.price - discount_amount)  # Minimum $0.50 for Stripe
                    metadata['discount_code'] = clean_code
                    metadata['discount_amount'] = str(discount_amount)
                    metadata['original_price'] = str(product.price)
                    metadata['discount_source'] = 'newsletter'
                else:
                    print(f"❌ No discount code found for: '{clean_code}'")
        
        # Create single line item with final price
        # Stripe has limits: name max 250 chars, description max 350 chars
        product_name = product.title[:250] if product.title else "User Manual"
        
        # Simple description with brand and model
        product_desc = f'{product.brand} {product.model}'
        if discount_amount > 0:
            product_desc += f' - Discount: ${discount_amount:.2f}'
        product_desc = product_desc[:350]  # Ensure within Stripe limit
        
        # Prepare product images for Stripe
        product_images = []
        if product.image_url:
            # Get first image from comma-separated list
            images = [img.strip() for img in product.image_url.split(',') if img.strip()]
            if images:
                first_image = images[0]
                # Ensure it's a full URL (Stripe requires https://)
                if first_image.startswith('http://') or first_image.startswith('https://'):
                    product_images = [first_image]
                elif first_image.startswith('/'):
                    # Convert relative path to full URL
                    product_images = [DOMAIN + first_image]
        
        # Build product_data with optional images
        product_data = {
            'name': product_name,
            'description': product_desc,
        }
        if product_images:
            product_data['images'] = product_images
        
        line_items = [{
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(final_price * 100),  # Convert to cents
                'product_data': product_data,
            },
            'quantity': 1,
        }]
        
        print(f"💳 Creating Stripe session for product {product.id}: {product_name[:50]}... Price: ${final_price}")
        
        # Create Stripe checkout session
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=DOMAIN + f'/manuals/{product.slug}',
                customer_email=None,  # Let Stripe collect email
                metadata=metadata
            )
            
            print(f"✅ Stripe session created: {checkout_session.id}")
            return {"url": checkout_session.url}
        except Exception as stripe_error:
            print(f"❌ Stripe error: {stripe_error}")
            print(f"   Product: {product.id}, Title: {product.title}")
            print(f"   Price: {final_price}, Metadata: {metadata}")
            raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(stripe_error)}")
    finally:
        session.close()


@orders_router.post("/create-multi-checkout-session")
async def create_multi_checkout_session(request: CreateMultiCheckoutSessionRequest):
    """Create Stripe checkout session for multiple products"""
    session = get_session()
    try:
        print(f"📦 Multi-checkout request: {len(request.product_ids)} products, discount: '{request.discount_code}'")
        print(f"🔑 Stripe API Key status: {'SET' if stripe.api_key else 'NOT SET'}")
        print(f"🔑 Stripe API Key prefix: {stripe.api_key[:20] if stripe.api_key else 'N/A'}")
        print(f"🔑 Is placeholder: {stripe.api_key == 'sk_test_placeholder'}")
        print(f"🌐 DOMAIN: {DOMAIN}")
        
        # Validate Stripe is configured
        if not stripe.api_key or stripe.api_key == "sk_test_placeholder":
            error_msg = f"Payment system not configured. Stripe key: {stripe.api_key[:30] if stripe.api_key else 'NOT SET'}"
            print(f"❌ {error_msg}")
            raise HTTPException(
                status_code=500, 
                detail=error_msg
            )
        
        # Validate we have product IDs
        if not request.product_ids or len(request.product_ids) == 0:
            raise HTTPException(status_code=400, detail="No products in cart")
        
        # Get all products
        products = session.query(Product).filter(Product.id.in_(request.product_ids)).all()
        if not products:
            raise HTTPException(status_code=404, detail="Products not found")
        
        # Validate all products have valid prices
        for product in products:
            if not product.price or product.price <= 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Product {product.id} ({product.title[:50]}) has invalid price: {product.price}"
                )
        
        print(f"✅ Found {len(products)} products in database")
        
        # Validate discount code if provided (and not empty string)
        discount_amount = 0
        discount_code_obj = None
        discount_source = None
        
        if request.discount_code and request.discount_code.strip():
            # Clean and normalize the code
            clean_code = request.discount_code.strip().upper()
            print(f"🎫 Validating discount code: '{clean_code}'")
            
            # First check regular discount codes
            discount_code_obj = session.query(DiscountCode).filter(
                DiscountCode.code == clean_code
            ).first()
            
            if discount_code_obj:
                print(f"✅ Found regular discount code: {discount_code_obj.code}")
                is_valid, message = discount_code_obj.is_valid()
                if not is_valid:
                    raise HTTPException(status_code=400, detail=message)
                discount_source = 'discount_code'
            else:
                # Check newsletter discount codes (10% off)
                newsletter = session.query(Newsletter).filter(
                    Newsletter.discount_code == clean_code,
                    Newsletter.is_active == True
                ).first()
                
                if newsletter:
                    print(f"✅ Found newsletter discount code: {newsletter.discount_code}")
                    discount_source = 'newsletter'
                else:
                    print(f"❌ No discount code found for: '{clean_code}'")
                    raise HTTPException(status_code=400, detail="Invalid discount code")
        
        # Calculate total
        subtotal = sum(p.price for p in products)
        
        # Apply discount
        if discount_source == 'discount_code' and discount_code_obj:
            discount_amount = discount_code_obj.calculate_discount(subtotal)
        elif discount_source == 'newsletter':
            discount_amount = subtotal * 0.10  # 10% off for newsletter codes
        
        # Calculate expected total after discount
        expected_total = subtotal - discount_amount
        expected_total_cents = round(expected_total * 100)  # Total in cents
        
        # Calculate discount percentage to apply to each product
        discount_percentage = (discount_amount / subtotal) if subtotal > 0 else 0
        
        # Create line items for each product with proportional discount applied
        # Track accumulated total to fix rounding errors on last item
        line_items = []
        accumulated_cents = 0
        
        for idx, product in enumerate(products):
            try:
                is_last_item = (idx == len(products) - 1)
                
                if is_last_item:
                    # Last item gets the remaining amount to ensure exact total
                    remaining_cents = expected_total_cents - accumulated_cents
                    final_price_cents = max(50, remaining_cents)  # Minimum $0.50
                    final_price = final_price_cents / 100
                else:
                    # Calculate discounted price for this product
                    product_discount = product.price * discount_percentage
                    final_price = product.price - product_discount
                    final_price_cents = round(final_price * 100)
                    final_price_cents = max(50, final_price_cents)  # Minimum $0.50
                    final_price = final_price_cents / 100
                    accumulated_cents += final_price_cents
                
                # Calculate actual discount for display
                product_discount = product.price - final_price
                
                # Stripe has limits: name max 250 chars, description max 350 chars
                product_name = product.title[:250] if product.title else "User Manual"
                
                # Simple description with brand and model
                product_desc = f'{product.brand} {product.model}'
                if product_discount > 0.01:  # Only show if meaningful discount
                    product_desc += f' - Discount: ${product_discount:.2f}'
                product_desc = product_desc[:350]
                
                # Prepare product images for Stripe
                product_images = []
                if product.image_url:
                    # Get first image from comma-separated list
                    images = [img.strip() for img in product.image_url.split(',') if img.strip()]
                    if images:
                        first_image = images[0]
                        # Ensure it's a full URL (Stripe requires https://)
                        if first_image.startswith('http://') or first_image.startswith('https://'):
                            product_images = [first_image]
                        elif first_image.startswith('/'):
                            # Convert relative path to full URL
                            product_images = [DOMAIN + first_image]
                
                # Build product_data with optional images
                product_data = {
                    'name': product_name,
                    'description': product_desc,
                }
                if product_images:
                    product_data['images'] = product_images
                
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': final_price_cents,
                        'product_data': product_data,
                    },
                    'quantity': 1,
                })
                
                print(f"  ✓ Added line item: {product_name[:50]}... ${final_price:.2f} ({final_price_cents}¢)")
            except Exception as item_error:
                print(f"  ❌ Error creating line item for product {product.id}: {item_error}")
                raise
        
        # Verify total matches expected
        actual_total_cents = sum(item['price_data']['unit_amount'] for item in line_items)
        actual_total = actual_total_cents / 100
        print(f"🛒 Multi-checkout: {len(products)} products")
        print(f"   Subtotal: ${subtotal:.2f}, Discount: ${discount_amount:.2f}")
        print(f"   Expected total: ${expected_total:.2f} ({expected_total_cents}¢)")
        print(f"   Actual total: ${actual_total:.2f} ({actual_total_cents}¢)")
        
        # Create Stripe checkout session with multiple items
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=DOMAIN + '/cart',
                customer_email=None,  # Let Stripe collect email
                metadata={
                    'product_ids': ','.join(map(str, request.product_ids)),
                    'is_multi_product': 'true',
                    'discount_code': request.discount_code or '',
                    'discount_amount': str(discount_amount),
                    'original_total': str(subtotal)
                }
            )
            
            print(f"✅ Multi-checkout session created: {checkout_session.id}")
            return {"url": checkout_session.url}
        except Exception as stripe_error:
            print(f"❌ Stripe multi-checkout error: {stripe_error}")
            print(f"   Products: {request.product_ids}")
            print(f"   Subtotal: {subtotal}, Discount: {discount_amount}")
            print(f"   Line items count: {len(line_items)}")
            raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(stripe_error)}")
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        error_details = {
            'error': str(e),
            'error_type': type(e).__name__,
            'stripe_configured': stripe.api_key != "sk_test_placeholder" if stripe.api_key else False,
            'stripe_key_prefix': stripe.api_key[:20] if stripe.api_key else None,
            'domain': DOMAIN,
            'product_count': len(request.product_ids) if request.product_ids else 0
        }
        print(f"❌ Multi-checkout error: {e}")
        print(f"   Request: product_ids={request.product_ids}, discount_code='{request.discount_code}'")
        print(f"   Error details: {error_details}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)} | Config: {error_details}")
    finally:
        session.close()


@orders_router.post("/process/{order_id}")
async def process_order_manual(order_id: int, current_user: User = Depends(get_current_admin_user)):
    """
    Manually process an order - download PDF, upload to Google Drive, send email
    (Admin only - for testing or manual processing)
    """
    from pdf_manager import PDFManager
    from google_drive_manager import GoogleDriveManager
    from pathlib import Path
    
    db_session = get_session()
    try:
        # Get order
        order = db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get product
        product = db_session.query(Product).filter(Product.id == order.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        google_drive_link = product.google_drive_link
        
        # If no link exists, download PDF and upload to Google Drive
        if not google_drive_link and product.pdf_url:
            print(f"📥 Processing order {order.id} - downloading and uploading PDF...")
            
            # Download PDF
            pdf_manager = PDFManager()
            pdf_result = pdf_manager.download_single_pdf(
                product_id=product.id,
                title=product.title,
                pdf_url=product.pdf_url
            )
            
            if pdf_result and pdf_result['success']:
                # Upload to Google Drive
                drive_manager = GoogleDriveManager()
                if drive_manager.service:
                    google_drive_link = drive_manager.upload_pdf(
                        file_path=Path(pdf_result['pdf_path']),
                        product_id=product.id,
                        title=product.title,
                        check_existing=False
                    )
                    
                    if google_drive_link:
                        # Save link to database
                        product.google_drive_link = google_drive_link
                        product.pdf_processed = True
                        order.download_link = google_drive_link
                        db_session.commit()
                        print(f"✅ PDF uploaded and link saved for product {product.id}")
                    else:
                        return {"success": False, "error": "Failed to upload PDF to Google Drive"}
                else:
                    return {"success": False, "error": "Google Drive not configured"}
            else:
                return {"success": False, "error": "Failed to download PDF"}
        else:
            # Use existing link
            if not order.download_link:
                order.download_link = google_drive_link
                db_session.commit()
        
        # Send email with link
        if google_drive_link:
            try:
                send_manual_ready_email(
                    to_email=order.email,
                    order_id=order.id,
                    product_title=product.title,
                    download_link=google_drive_link
                )
                print(f"✅ Manual link sent to {order.email}")
                return {"success": True, "message": "Email sent successfully", "link": google_drive_link}
            except Exception as e:
                print(f"Failed to send email: {e}")
                return {"success": False, "error": f"Failed to send email: {str(e)}"}
        else:
            return {"success": False, "error": "No download link available"}
            
    except Exception as e:
        print(f"Error processing order: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()


@orders_router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    print("="*80)
    print("🔔 WEBHOOK RECEIVED!")
    print("="*80)
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    print(f"Payload length: {len(payload)}")
    print(f"Signature present: {bool(sig_header)}")
    
    try:
        # Verify webhook signature (in production, use STRIPE_WEBHOOK_SECRET)
        if STRIPE_WEBHOOK_SECRET != "whsec_your_webhook_secret_here":
            print(f"🔐 Verifying webhook signature...")
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            print(f"✅ Signature verified!")
        else:
            # Development mode: skip signature verification
            print(f"⚠️  Development mode - skipping signature verification")
            import json
            event = json.loads(payload)
        
        print(f"📨 Event type: {event['type']}")
        
        # Handle successful payment
        if event['type'] == 'checkout.session.completed':
            print(f"💳 Processing payment completion...")
            session_data = event['data']['object']
            
            # Get session details from database
            db_session = get_session()
            try:
                customer_email = session_data['customer_details']['email']
                payment_intent = session_data['payment_intent']
                
                # Check if this is multi-product order
                metadata = session_data.get('metadata', {})
                is_multi = metadata.get('is_multi_product') == 'true'
                
                if is_multi:
                    # Multi-product order
                    print(f"🛒 Multi-product order detected")
                    
                    if 'product_ids' not in metadata:
                        print(f"❌ No product_ids in metadata: {metadata}")
                        return {"status": "error", "message": "No product_ids in metadata"}
                    
                    product_ids = [int(pid) for pid in metadata['product_ids'].split(',')]
                    print(f"📦 Processing multi-product order for products: {product_ids}")
                    
                    # Check if orders already exist
                    existing = db_session.query(Order).filter(Order.paypal_order_id == payment_intent).first()
                    if existing:
                        print(f"⚠️  Orders already exist for payment_intent {payment_intent} - skipping")
                        return {"status": "ok", "message": "Orders already exist"}
                    
                    # Get all products
                    products = db_session.query(Product).filter(Product.id.in_(product_ids)).all()
                    if not products:
                        print(f"❌ No products found for IDs: {product_ids}")
                        return {"status": "error", "message": "Products not found"}
                    
                    # Create separate order for each product
                    created_orders = []
                    for product in products:
                        order = Order(
                            email=customer_email,
                            product_id=product.id,
                            price=product.price,
                            paypal_order_id=payment_intent,
                            status="completed"
                        )
                        db_session.add(order)
                        created_orders.append(order)
                    
                    db_session.commit()
                    
                    # Refresh orders to get IDs
                    for order in created_orders:
                        db_session.refresh(order)
                    
                    print(f"✅ Created {len(created_orders)} orders for multi-product purchase")
                    
                    # Send confirmation email for all products
                    try:
                        total_price = sum(p.price for p in products)
                        product_titles = ", ".join([p.title for p in products])
                        send_order_confirmation_email(
                            to_email=customer_email,
                            order_id=f"MULTI-{payment_intent[:8]}",
                            product_title=f"{len(products)} products: {product_titles}",
                            price=total_price
                        )
                    except Exception as e:
                        print(f"Failed to send confirmation email: {e}")
                    
                    # Process and send each manual
                    all_links_sent = True
                    for product in products:
                        try:
                            google_drive_link = product.google_drive_link
                            
                            if not google_drive_link and product.pdf_url:
                                print(f"📥 Processing PDF for product {product.id}...")
                                
                                try:
                                    from railway_pdf_processor import RailwayPDFProcessor
                                    processor = RailwayPDFProcessor()
                                    
                                    if processor.process_product(product.id):
                                        db_session.refresh(product)
                                        google_drive_link = product.google_drive_link
                                        print(f"✅ PDF processed for product {product.id}")
                                    else:
                                        google_drive_link = product.pdf_url
                                    
                                    processor.close()
                                except Exception as e:
                                    print(f"❌ PDF processor error: {e}")
                                    google_drive_link = product.pdf_url
                            
                            if google_drive_link:
                                # Update order with download link
                                order_to_update = db_session.query(Order).filter(
                                    Order.paypal_order_id == payment_intent,
                                    Order.product_id == product.id
                                ).first()
                                if order_to_update:
                                    order_to_update.download_link = google_drive_link
                                    db_session.commit()
                                
                                send_manual_ready_email(
                                    to_email=customer_email,
                                    order_id=order_to_update.id if order_to_update else product.id,
                                    product_title=product.title,
                                    download_link=google_drive_link
                                )
                                print(f"✅ Sent manual link for {product.title}")
                            else:
                                print(f"⚠️  No download link for product {product.id}")
                                all_links_sent = False
                        except Exception as e:
                            print(f"Failed to process manual for product {product.id}: {e}")
                            all_links_sent = False
                    
                    # Send admin notification for multi-product order
                    try:
                        total_price = sum(p.price for p in products)
                        product_titles = ", ".join([p.title for p in products])
                        send_admin_order_notification(
                            order_id=f"MULTI-{payment_intent[:8]}",
                            customer_email=customer_email,
                            product_title=f"{len(products)} products: {product_titles}",
                            price=total_price,
                            link_sent=all_links_sent
                        )
                    except Exception as e:
                        print(f"Failed to send admin notification: {e}")
                    
                    return {"status": "ok", "message": f"Multi-product order processed ({len(products)} products)"}
                
                # Single product order
                if 'product_id' not in metadata:
                    print(f"❌ No product_id in metadata: {metadata}")
                    return {"status": "error", "message": "No product_id in metadata"}
                
                product_id = int(metadata['product_id'])
                
                # Get product
                product = db_session.query(Product).filter(Product.id == product_id).first()
                if not product:
                    print(f"Product {product_id} not found")
                    return {"status": "error", "message": "Product not found"}
                
                # Check if order already exists
                existing = db_session.query(Order).filter(Order.paypal_order_id == payment_intent).first()
                if existing:
                    print(f"⚠️  Order already exists for payment_intent {payment_intent} - skipping")
                    return {"status": "ok", "message": "Order already exists"}
                
                print(f"💳 Creating new order for payment_intent: {payment_intent}")
                
                # Create order
                order = Order(
                    email=customer_email,
                    product_id=product.id,
                    price=product.price,
                    paypal_order_id=payment_intent,  # Store Stripe payment_intent as order ID
                    status="completed"
                )
                db_session.add(order)
                db_session.commit()
                db_session.refresh(order)
                
                # Send confirmation email
                try:
                    send_order_confirmation_email(
                        to_email=customer_email,
                        order_id=order.id,
                        product_title=product.title,
                        price=product.price
                    )
                except Exception as e:
                    print(f"Failed to send confirmation email: {e}")
                
                # Send Google Drive link - download and upload if needed
                link_was_sent = False
                try:
                    google_drive_link = product.google_drive_link
                    
                    # If no link exists, download PDF and upload to Google Drive
                    if not google_drive_link and product.pdf_url:
                        print(f"📥 First purchase of product {product.id} - processing PDF...")
                        
                        # Use Railway PDF processor for seamless cloud operation
                        try:
                            from railway_pdf_processor import RailwayPDFProcessor
                            processor = RailwayPDFProcessor()
                            
                            if processor.process_product(product.id):
                                # Refresh product from database to get updated google_drive_link
                                db_session.refresh(product)
                                google_drive_link = product.google_drive_link
                                print(f"✅ PDF processed and uploaded for product {product.id}")
                            else:
                                print(f"❌ Failed to process PDF - using pdf_url fallback")
                                google_drive_link = product.pdf_url
                            
                            processor.close()
                            
                        except Exception as e:
                            print(f"❌ Railway processor error: {e}")
                            google_drive_link = product.pdf_url  # Fallback to direct link
                    
                    # Send email with link and save to order
                    if google_drive_link:
                        # Save link to order so customer can see it in "My Orders"
                        order.download_link = google_drive_link
                        db_session.commit()
                        
                        send_manual_ready_email(
                            to_email=customer_email,
                            order_id=order.id,
                            product_title=product.title,
                            download_link=google_drive_link
                        )
                        print(f"✅ Sent manual link to {customer_email}")
                        link_was_sent = True
                    else:
                        print(f"⚠️  No download link available for product {product.id}")
                        link_was_sent = False
                        
                except Exception as e:
                    print(f"Failed to process manual delivery: {e}")
                    import traceback
                    traceback.print_exc()
                    link_was_sent = False
                
                # Send admin notification with link status
                try:
                    send_admin_order_notification(
                        order_id=order.id,
                        customer_email=customer_email,
                        product_title=product.title,
                        price=product.price,
                        link_sent=link_was_sent
                    )
                except Exception as e:
                    print(f"Failed to send admin notification: {e}")
                
                print(f"Order {order.id} created for {customer_email}")
                
            finally:
                db_session.close()
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Newsletter endpoints
newsletter_router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr


class ValidateCodeRequest(BaseModel):
    code: str


def generate_discount_code():
    """Generate unique discount code"""
    return 'WELCOME' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


@newsletter_router.post("/subscribe")
async def subscribe_newsletter(data: NewsletterSubscribeRequest):
    """Subscribe to newsletter and get 10% discount code"""
    session = get_session()
    
    try:
        # Check if already subscribed
        existing = session.query(Newsletter).filter(Newsletter.email == data.email).first()
        
        if existing:
            if existing.is_active:
                return {
                    "success": True,
                    "message": "You're already subscribed!",
                    "discount_code": existing.discount_code
                }
            else:
                # Reactivate subscription
                existing.is_active = True
                session.commit()
                return {
                    "success": True,
                    "message": "Welcome back! Your subscription has been reactivated.",
                    "discount_code": existing.discount_code
                }
        
        # Create new subscription
        discount_code = generate_discount_code()
        
        subscription = Newsletter(
            email=data.email,
            discount_code=discount_code,
            is_active=True
        )
        
        session.add(subscription)
        session.commit()
        
        # Send welcome email with discount code
        print(f"📧 Attempting to send welcome email to {data.email} with code {discount_code}...")
        try:
            result = send_welcome_newsletter_email(data.email, discount_code)
            if result:
                print(f"✅ Welcome email sent successfully to {data.email}")
            else:
                print(f"⚠️ Welcome email failed to send to {data.email}")
        except Exception as e:
            print(f"❌ Exception sending welcome email: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "success": True,
            "message": "Thank you for subscribing!",
            "discount_code": discount_code
        }
        
    except Exception as e:
        session.rollback()
        print(f"Newsletter subscription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")
    finally:
        session.close()

@newsletter_router.post("/validate-code")
async def validate_discount_code(data: ValidateCodeRequest):
    """Validate discount code"""
    session = get_session()
    
    try:
        # Check if code exists and is active
        subscription = session.query(Newsletter).filter(
            Newsletter.discount_code == data.code,
            Newsletter.is_active == True
        ).first()
        
        if subscription:
            return {
                "valid": True,
                "percent": 10,  # 10% discount
                "message": "Discount code valid!"
            }
        else:
            return {
                "valid": False,
                "message": "Invalid discount code"
            }
    except Exception as e:
        print(f"Code validation error: {e}")
        return {
            "valid": False,
            "message": "Error validating code"
        }
    finally:
        session.close()


# Import tracking global variables
import_status = {
    "active": False,
    "progress": 0,
    "total": 0,
    "current_batch": 0,
    "started_at": None,
    "estimated_completion": None,
    "errors": [],
    "last_update": None
}

# Security mode - change to False for production!
IMPORT_TEST_MODE = True  # Set to False on live website


class ImportStatusResponse(BaseModel):
    active: bool
    progress: int
    total: int
    current_batch: int
    percentage: float
    started_at: Optional[str]
    estimated_completion: Optional[str]
    errors: list
    last_update: Optional[str]


@import_router.get("/status", response_model=ImportStatusResponse)
async def get_import_status():
    """Get current import progress status"""
    global import_status
    
    percentage = 0
    if import_status["total"] > 0:
        percentage = (import_status["progress"] / import_status["total"]) * 100
    
    return ImportStatusResponse(
        active=import_status["active"],
        progress=import_status["progress"],
        total=import_status["total"],
        current_batch=import_status["current_batch"],
        percentage=round(percentage, 1),
        started_at=import_status["started_at"],
        estimated_completion=import_status["estimated_completion"],
        errors=import_status["errors"],
        last_update=import_status["last_update"]
    )


@import_router.get("/csv-files")
async def get_csv_files(current_user: dict = Depends(get_current_admin_user) if not IMPORT_TEST_MODE else None):
    """List available CSV files for import"""
    import glob
    import pandas as pd
    
    # Skip auth check in test mode
    if not IMPORT_TEST_MODE and not current_user:
        raise HTTPException(status_code=401, detail="Admin access required")
    
    try:
        csv_files = glob.glob("*.csv")
        file_info = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                file_info.append({
                    "name": csv_file,
                    "products": len(df),
                    "columns": list(df.columns),
                    "size": os.path.getsize(csv_file)
                })
            except Exception as e:
                file_info.append({
                    "name": csv_file,
                    "products": 0,
                    "columns": [],
                    "size": os.path.getsize(csv_file),
                    "error": str(e)
                })
        
        return {"files": file_info}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan CSV files: {str(e)}")


@import_router.post("/start")
async def start_bulk_import(
    request: Request,
    current_user: dict = Depends(get_current_admin_user) if not IMPORT_TEST_MODE else None
):
    """Start bulk import process"""
    global import_status
    
    # Skip auth check in test mode
    if not IMPORT_TEST_MODE and not current_user:
        raise HTTPException(status_code=401, detail="Admin access required")
    
    if import_status["active"]:
        raise HTTPException(
            status_code=400, 
            detail="Import already in progress"
        )
    
    # Get CSV file from request body
    try:
        body = await request.json()
        selected_csv_file = body.get("csv_file")
    except:
        selected_csv_file = None
    
    # Reset status
    import_status.update({
        "active": True,
        "progress": 0,
        "total": 0,
        "current_batch": 0,
        "started_at": datetime.now().isoformat(),
        "estimated_completion": None,
        "errors": [],
        "last_update": datetime.now().isoformat(),
        "selected_file": selected_csv_file
    })
    
    # Start the actual import process in background
    asyncio.create_task(run_bulk_import(selected_csv_file))
    
    return {"message": f"Import started{' from ' + selected_csv_file if selected_csv_file else ''}", "status": "initiated"}
    
    return {"message": "Import started", "status": "initiated"}


async def run_bulk_import(selected_csv_file=None):
    """Run the actual bulk import process"""
    global import_status
    
    try:
        from bulk_import_products import ProductImporter
        import os
        
        # Use selected file or find CSV file automatically
        if selected_csv_file and os.path.exists(selected_csv_file):
            csv_file = selected_csv_file
        else:
            # Check for CSV file
            csv_files = [
                "products_100k_ready.csv",
                "products_example.csv", 
                "products.csv"
            ]
            
            csv_file = None
            for filename in csv_files:
                if os.path.exists(filename):
                    csv_file = filename
                    break
        
        if not csv_file:
            import_status.update({
                "active": False,
                "errors": [{"time": datetime.now().isoformat(), "error": "No CSV file found for import"}],
                "last_update": datetime.now().isoformat()
            })
            return
        
        # Create importer and run import
        importer = ProductImporter()
        
        # Update status with file info
        import pandas as pd
        df = pd.read_csv(csv_file)
        import_status.update({
            "total": len(df),
            "last_update": datetime.now().isoformat()
        })
        
        # Run import with progress tracking
        success = await asyncio.to_thread(importer.import_from_csv_with_progress, csv_file)
        
        if success:
            import_status.update({
                "active": False,
                "progress": import_status["total"],
                "percentage": 100,
                "last_update": datetime.now().isoformat()
            })
        else:
            import_status.update({
                "active": False,
                "errors": import_status["errors"] + [{"time": datetime.now().isoformat(), "error": "Import failed"}],
                "last_update": datetime.now().isoformat()
            })
            
    except Exception as e:
        import_status.update({
            "active": False,
            "errors": import_status["errors"] + [{"time": datetime.now().isoformat(), "error": f"Import error: {str(e)}"}],
            "last_update": datetime.now().isoformat()
        })


@import_router.post("/stop")
async def stop_bulk_import(current_user: dict = Depends(get_current_admin_user) if not IMPORT_TEST_MODE else None):
    """Stop bulk import process"""
    global import_status
    
    # Skip auth check in test mode
    if not IMPORT_TEST_MODE and not current_user:
        raise HTTPException(status_code=401, detail="Admin access required")
    
    import_status["active"] = False
    import_status["last_update"] = datetime.now().isoformat()
    
    return {"message": "Import stopped", "status": "stopped"}


def update_import_progress(progress: int, total: int, current_batch: int = 0, error: str = None):
    """Update import progress (called by import scripts)"""
    global import_status
    
    import_status.update({
        "progress": progress,
        "total": total,
        "current_batch": current_batch,
        "last_update": datetime.now().isoformat()
    })
    
    if error:
        import_status["errors"].append({
            "time": datetime.now().isoformat(),
            "error": error
        })
    
    # Estimate completion time
    if progress > 0 and import_status["started_at"]:
        start_time = datetime.fromisoformat(import_status["started_at"])
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if elapsed > 0:
            rate = progress / elapsed  # items per second
            remaining = total - progress
            estimated_seconds = remaining / rate if rate > 0 else 0
            
            completion_time = datetime.now() + timedelta(seconds=estimated_seconds)
            import_status["estimated_completion"] = completion_time.isoformat()
    
    print(f"📊 Import Progress: {progress}/{total} ({current_batch} batch)")


# Export routers
__all__ = ["router", "orders_router", "import_router"]