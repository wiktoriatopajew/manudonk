"""
Email Marketing API endpoints
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from database.models import Newsletter, EmailCampaign, EmailTracking, get_session, User
from auth import get_current_admin_user
from email_utils import send_marketing_campaign_email

email_marketing_router = APIRouter(prefix="/api/email-marketing", tags=["email_marketing"])

# Domain configuration
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")


@email_marketing_router.get("/subscribers")
async def get_subscribers(
    segment: str = "all",  # all, purchased, not_purchased, active
    user: User = Depends(get_current_admin_user)
):
    """Get list of subscribers (admin only)"""
    session = get_session()
    
    try:
        query = session.query(Newsletter)
        
        # Apply filters based on segment
        if segment == "purchased":
            query = query.filter(Newsletter.has_purchased == True)
        elif segment == "not_purchased":
            query = query.filter(Newsletter.has_purchased == False)
        elif segment == "active":
            query = query.filter(Newsletter.is_active == True)
        
        subscribers = query.all()
        
        return {
            "success": True,
            "count": len(subscribers),
            "subscribers": [
                {
                    "id": s.id,
                    "email": s.email,
                    "discount_code": s.discount_code,
                    "subscribed_at": s.subscribed_at.isoformat() if s.subscribed_at else None,
                    "is_active": s.is_active,
                    "has_purchased": s.has_purchased,
                    "last_reminder_sent": s.last_reminder_sent.isoformat() if s.last_reminder_sent else None
                }
                for s in subscribers
            ]
        }
    except Exception as e:
        print(f"Error fetching subscribers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscribers")
    finally:
        session.close()


class CreateCampaignRequest(BaseModel):
    name: str
    subject: str
    html_content: str
    segment: str = "all"


@email_marketing_router.post("/campaigns")
async def create_campaign(
    data: CreateCampaignRequest,
    user: User = Depends(get_current_admin_user)
):
    """Create new email campaign (admin only)"""
    session = get_session()
    
    try:
        campaign = EmailCampaign(
            name=data.name,
            subject=data.subject,
            html_content=data.html_content,
            segment=data.segment,
            status='draft'
        )
        
        session.add(campaign)
        session.commit()
        
        return {
            "success": True,
            "campaign_id": campaign.id,
            "message": "Campaign created successfully"
        }
    except Exception as e:
        session.rollback()
        print(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to create campaign")
    finally:
        session.close()


@email_marketing_router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    user: User = Depends(get_current_admin_user)
):
    """Send email campaign to selected segment (admin only)"""
    session = get_session()
    
    try:
        # Get campaign
        campaign = session.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.status == 'sent':
            raise HTTPException(status_code=400, detail="Campaign already sent")
        
        # Get subscribers based on segment
        query = session.query(Newsletter).filter(Newsletter.is_active == True)
        
        if campaign.segment == "purchased":
            query = query.filter(Newsletter.has_purchased == True)
        elif campaign.segment == "not_purchased":
            query = query.filter(Newsletter.has_purchased == False)
        
        subscribers = query.all()
        
        if not subscribers:
            raise HTTPException(status_code=400, detail="No subscribers in selected segment")
        
        # Send emails
        sent_count = 0
        for subscriber in subscribers:
            try:
                # Create tracking token
                tracking = EmailTracking(
                    campaign_id=campaign.id,
                    subscriber_id=subscriber.id,
                    email=subscriber.email,
                    tracking_token=EmailTracking.generate_token()
                )
                session.add(tracking)
                session.commit()
                
                # Replace {{domain}} placeholder with actual domain
                personalized_content = campaign.html_content.replace("{{domain}}", DOMAIN)
                
                # Send email with tracking
                result = send_marketing_campaign_email(
                    subscriber.email,
                    campaign.subject,
                    personalized_content,
                    tracking.tracking_token
                )
                
                if result:
                    sent_count += 1
                
            except Exception as e:
                print(f"Error sending to {subscriber.email}: {e}")
                continue
        
        # Update campaign status
        campaign.status = 'sent'
        campaign.sent_at = datetime.utcnow()
        campaign.sent_count = sent_count
        session.commit()
        
        return {
            "success": True,
            "sent_count": sent_count,
            "total_subscribers": len(subscribers),
            "message": f"Campaign sent to {sent_count} subscribers"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        print(f"Error sending campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to send campaign")
    finally:
        session.close()


@email_marketing_router.get("/campaigns")
async def get_campaigns(user: User = Depends(get_current_admin_user)):
    """Get list of all campaigns (admin only)"""
    session = get_session()
    
    try:
        campaigns = session.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).all()
        
        return {
            "success": True,
            "campaigns": [
                {
                    "id": c.id,
                    "name": c.name,
                    "subject": c.subject,
                    "segment": c.segment,
                    "status": c.status,
                    "sent_count": c.sent_count,
                    "sent_at": c.sent_at.isoformat() if c.sent_at else None,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in campaigns
            ]
        }
    except Exception as e:
        print(f"Error fetching campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")
    finally:
        session.close()


@email_marketing_router.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: int,
    user: User = Depends(get_current_admin_user)
):
    """Get campaign statistics (admin only)"""
    session = get_session()
    
    try:
        campaign = session.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get tracking stats
        total_sent = session.query(EmailTracking).filter(
            EmailTracking.campaign_id == campaign_id
        ).count()
        
        opened_count = session.query(EmailTracking).filter(
            EmailTracking.campaign_id == campaign_id,
            EmailTracking.opened == True
        ).count()
        
        clicked_count = session.query(EmailTracking).filter(
            EmailTracking.campaign_id == campaign_id,
            EmailTracking.clicked == True
        ).count()
        
        # Calculate rates
        open_rate = (opened_count / total_sent * 100) if total_sent > 0 else 0
        click_rate = (clicked_count / total_sent * 100) if total_sent > 0 else 0
        
        return {
            "success": True,
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "stats": {
                "total_sent": total_sent,
                "opened": opened_count,
                "clicked": clicked_count,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")
    finally:
        session.close()
