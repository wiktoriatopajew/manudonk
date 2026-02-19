"""
Discount code management routes for admin panel
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database.models import DiscountCode, Newsletter, get_session
from auth import get_current_admin_user

router = APIRouter(prefix="/api/discount-codes", tags=["discount-codes"])


class DiscountCodeCreate(BaseModel):
    code: str
    type: str  # 'percentage' or 'fixed'
    value: float
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None


class DiscountCodeResponse(BaseModel):
    id: int
    code: str
    type: str
    value: float
    description: Optional[str]
    expires_at: Optional[datetime]
    max_uses: Optional[int]
    used_count: int
    active: bool
    created_at: datetime
    created_by: str
    is_valid: bool
    validation_message: str


@router.get("/", response_model=List[DiscountCodeResponse])
async def list_discount_codes(current_user = Depends(get_current_admin_user)):
    """Get all discount codes"""
    session = get_session()
    try:
        codes = session.query(DiscountCode).order_by(DiscountCode.created_at.desc()).all()
        
        result = []
        for code in codes:
            is_valid, message = code.is_valid()
            result.append({
                'id': code.id,
                'code': code.code,
                'type': code.type,
                'value': code.value,
                'description': code.description,
                'expires_at': code.expires_at,
                'max_uses': code.max_uses,
                'used_count': code.used_count,
                'active': code.active,
                'created_at': code.created_at,
                'created_by': code.created_by,
                'is_valid': is_valid,
                'validation_message': message
            })
        
        return result
    finally:
        session.close()


@router.post("/", response_model=DiscountCodeResponse)
async def create_discount_code(
    data: DiscountCodeCreate,
    current_user = Depends(get_current_admin_user)
):
    """Create a new discount code"""
    session = get_session()
    try:
        # Check if code already exists
        existing = session.query(DiscountCode).filter(
            DiscountCode.code == data.code.upper()
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Discount code already exists")
        
        # Validate type
        if data.type not in ['percentage', 'fixed']:
            raise HTTPException(status_code=400, detail="Type must be 'percentage' or 'fixed'")
        
        # Validate value
        if data.type == 'percentage' and (data.value <= 0 or data.value > 100):
            raise HTTPException(status_code=400, detail="Percentage must be between 0 and 100")
        
        if data.value <= 0:
            raise HTTPException(status_code=400, detail="Value must be positive")
        
        # Create discount code
        discount_code = DiscountCode(
            code=data.code.upper(),
            type=data.type,
            value=data.value,
            description=data.description,
            expires_at=data.expires_at,
            max_uses=data.max_uses,
            created_by=current_user.email
        )
        
        session.add(discount_code)
        session.commit()
        session.refresh(discount_code)
        
        is_valid, message = discount_code.is_valid()
        
        return {
            'id': discount_code.id,
            'code': discount_code.code,
            'type': discount_code.type,
            'value': discount_code.value,
            'description': discount_code.description,
            'expires_at': discount_code.expires_at,
            'max_uses': discount_code.max_uses,
            'used_count': discount_code.used_count,
            'active': discount_code.active,
            'created_at': discount_code.created_at,
            'created_by': discount_code.created_by,
            'is_valid': is_valid,
            'validation_message': message
        }
    finally:
        session.close()


@router.post("/{code_id}/toggle")
async def toggle_discount_code(
    code_id: int,
    current_user = Depends(get_current_admin_user)
):
    """Toggle discount code active status"""
    session = get_session()
    try:
        code = session.query(DiscountCode).filter(DiscountCode.id == code_id).first()
        
        if not code:
            raise HTTPException(status_code=404, detail="Discount code not found")
        
        code.active = not code.active
        session.commit()
        
        return {"success": True, "active": code.active}
    finally:
        session.close()


@router.delete("/{code_id}")
async def delete_discount_code(
    code_id: int,
    current_user = Depends(get_current_admin_user)
):
    """Delete a discount code"""
    session = get_session()
    try:
        code = session.query(DiscountCode).filter(DiscountCode.id == code_id).first()
        
        if not code:
            raise HTTPException(status_code=404, detail="Discount code not found")
        
        session.delete(code)
        session.commit()
        
        return {"success": True}
    finally:
        session.close()


@router.get("/validate/{code}")
async def validate_discount_code(code: str):
    """Validate a discount code (public endpoint) - checks both DiscountCode and Newsletter tables"""
    session = get_session()
    try:
        clean_code = code.strip().upper()
        print(f"🎫 Validating code: '{clean_code}'")
        
        # First check regular discount codes
        discount_code = session.query(DiscountCode).filter(
            DiscountCode.code == clean_code
        ).first()
        
        if discount_code:
            print(f"✅ Found regular discount code: {discount_code.code}")
            is_valid, message = discount_code.is_valid()
            
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)
            
            return {
                'valid': True,
                'type': discount_code.type,
                'value': discount_code.value,
                'code': discount_code.code
            }
        
        # Check newsletter discount codes (10% off)
        newsletter = session.query(Newsletter).filter(
            Newsletter.discount_code == clean_code,
            Newsletter.is_active == True
        ).first()
        
        if newsletter:
            print(f"✅ Found newsletter discount code: {newsletter.discount_code}")
            return {
                'valid': True,
                'type': 'percentage',
                'value': 10,  # 10% discount for newsletter codes
                'code': newsletter.discount_code
            }
        
        print(f"❌ No discount code found for: '{clean_code}'")
        raise HTTPException(status_code=404, detail="Invalid discount code")
        
    finally:
        session.close()


@router.post("/apply/{code}")
async def apply_discount_code(code: str, total_amount: float):
    """Calculate discount for a given amount (public endpoint)"""
    session = get_session()
    try:
        discount_code = session.query(DiscountCode).filter(
            DiscountCode.code == code.upper()
        ).first()
        
        if not discount_code:
            raise HTTPException(status_code=404, detail="Invalid discount code")
        
        is_valid, message = discount_code.is_valid()
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        discount_amount = discount_code.calculate_discount(total_amount)
        final_amount = total_amount - discount_amount
        
        # Increment usage count
        discount_code.used_count += 1
        session.commit()
        
        return {
            'code': discount_code.code,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'type': discount_code.type,
            'value': discount_code.value
        }
    finally:
        session.close()
