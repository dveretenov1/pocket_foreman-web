# api/app/routes/billing.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..services.auth import get_current_user
from ..services.billing.subscription import subscription_service
from ..services.billing.usage import usage_service
from ..services.billing.stripe_service import stripe_service
from ..models.user import User
from ..schemas import billing as schemas
import logging
from datetime import datetime
from ..models.subscription import UsageRecord, SubscriptionTier, UserSubscription, MonthlyUsageSummary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/subscription/tiers", response_model=List[schemas.SubscriptionTier])
async def get_subscription_tiers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available subscription tiers"""
    return await subscription_service.get_subscription_tiers(db)

@router.get("/subscription")
async def get_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user's subscription details and available tiers"""
    # Get all available tiers
    tiers = await subscription_service.get_subscription_tiers(db)
    tiers_data = [{
        "id": tier.id,
        "name": tier.name,
        "price_usd": float(tier.price_usd),
        "monthly_pft": tier.monthly_pft,
        "overage_pft_price": float(tier.overage_pft_price)
    } for tier in tiers]
    
    # Get current subscription
    subscription = await subscription_service.get_user_subscription(db, current_user.id)
    
    if not subscription:
        # Return all tiers with free tier as current
        free_tier = next((tier for tier in tiers if tier.name == "Free"), None)
        if not free_tier:
            raise HTTPException(status_code=500, detail="Free tier not found")
            
        return {
            "tier": {
                "id": free_tier.id,
                "name": free_tier.name,
                "price_usd": float(free_tier.price_usd),
                "monthly_pft": free_tier.monthly_pft,
                "overage_pft_price": float(free_tier.overage_pft_price)
            },
            "status": "active",
            "current_period_end": None,
            "available_tiers": tiers_data
        }
    
    tier = db.query(SubscriptionTier).get(subscription.tier_id)
    if not tier:
        raise HTTPException(status_code=500, detail="Subscription tier not found")
        
    return {
        "tier": {
            "id": tier.id,
            "name": tier.name,
            "price_usd": float(tier.price_usd),
            "monthly_pft": tier.monthly_pft,
            "overage_pft_price": float(tier.overage_pft_price)
        },
        "status": subscription.status,
        "current_period_end": subscription.current_period_end,
        "stripe_subscription_id": subscription.stripe_subscription_id,
        "available_tiers": tiers_data
    }

@router.post("/setup-intent")
async def create_setup_intent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a SetupIntent for adding a payment method"""
    client_secret = await stripe_service.create_setup_intent(db, current_user)
    return {"client_secret": client_secret}

@router.post("/subscription", response_model=schemas.SubscriptionResponse)
async def create_subscription(
    subscription: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update subscription"""
    try:
        # Create Stripe subscription
        stripe_sub = await stripe_service.create_subscription(
            db,
            current_user,
            subscription.tier_id,
            subscription.payment_method_id
        )
        
        # Create local subscription record
        db_subscription = await subscription_service.create_subscription(
            db,
            current_user.id,
            subscription.tier_id,
            stripe_subscription_id=stripe_sub["subscriptionId"]
        )
        
        tier = db.query(SubscriptionTier).get(subscription.tier_id)
        if not tier:
            raise HTTPException(status_code=404, detail="Tier not found")
            
        return {
            "subscription": db_subscription,
            "tier": tier,
            "client_secret": stripe_sub["clientSecret"]
        }
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create subscription: {str(e)}"
        )

@router.delete("/subscription")
async def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel current subscription"""
    await stripe_service.cancel_subscription(db, current_user)
    return {"status": "cancelled"}

@router.get("/payment-methods")
async def get_payment_methods(
    current_user: User = Depends(get_current_user)
):
    """Get user's saved payment methods"""
    return await stripe_service.get_payment_methods(current_user)

@router.get("/usage/current")
async def get_current_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current month's usage statistics"""
    return await usage_service.get_current_usage(db, current_user.id)

@router.get("/usage/{year}/{month}", response_model=schemas.MonthlyUsage)
async def get_monthly_usage(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage for a specific month"""
    usage = await usage_service.get_monthly_usage(db, current_user.id, year, month)
    if not usage:
        raise HTTPException(status_code=404, detail="No usage data found for this month")
    return usage

# Admin routes
@router.get("/admin/users/{user_id}/usage", response_model=schemas.UsageResponse)
async def get_user_usage(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Get usage for specific user"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return await usage_service.get_current_usage(db, user_id)

@router.get("/admin/usage/summary")
async def get_usage_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Get overall usage summary"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all monthly summaries for current month
    now = datetime.now()
    summaries = db.query(MonthlyUsageSummary).filter(
        MonthlyUsageSummary.year == now.year,
        MonthlyUsageSummary.month == now.month
    ).all()
    
    total_pft = sum(float(s.total_pft or 0) for s in summaries)
    total_cost = sum(float((s.base_cost_usd or 0) + (s.overage_cost_usd or 0)) for s in summaries)
    
    return {
        "total_users": len(summaries),
        "total_pft": total_pft,
        "total_cost_usd": total_cost,
        "average_pft_per_user": total_pft / len(summaries) if summaries else 0,
        "average_cost_per_user": total_cost / len(summaries) if summaries else 0
    }
