# api/app/services/billing/subscription.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
from ...models.subscription import SubscriptionTier, UserSubscription
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    PocketForeman Token (PFT) based subscription service
    
    Tiers are designed to provide better value at higher levels:
    - Basic: 5,000 PFT for $5 (1 PFT = $0.001)
    - Pro: 22,000 PFT for $20 (1 PFT ≈ $0.00091, 10% bonus)
    - Enterprise: 48,000 PFT for $40 (1 PFT ≈ $0.00083, 20% bonus)
    """
    
    DEFAULT_TIERS = [
        {
            "name": "Free",
            "price_usd": Decimal('0.00'),
            "monthly_pft": 1000,              # 1,000 PFT free
            "overage_pft_price": Decimal('0.0015')  # $0.0015 per additional PFT
        },
        {
            "name": "Basic",
            "price_usd": Decimal('5.00'),
            "monthly_pft": 5000,              # 5,000 PFT = $5
            "overage_pft_price": Decimal('0.0012')  # $0.0012 per additional PFT
        },
        {
            "name": "Pro",
            "price_usd": Decimal('20.00'),
            "monthly_pft": 22000,             # 22,000 PFT = $20 (10% bonus)
            "overage_pft_price": Decimal('0.0011')  # $0.0011 per additional PFT
        },
        {
            "name": "Enterprise",
            "price_usd": Decimal('40.00'),
            "monthly_pft": 48000,             # 48,000 PFT = $40 (20% bonus)
            "overage_pft_price": Decimal('0.001')   # $0.001 per additional PFT
        }
    ]

    @staticmethod
    async def initialize_tiers(db: Session):
        """Initialize default subscription tiers"""
        try:
            existing_tiers = db.query(SubscriptionTier).all()
            if not existing_tiers:
                for tier_data in SubscriptionService.DEFAULT_TIERS:
                    tier = SubscriptionTier(**tier_data)
                    db.add(tier)
                db.commit()
                logger.info("Default subscription tiers created")
        except Exception as e:
            logger.error(f"Error initializing subscription tiers: {str(e)}")
            db.rollback()
            raise

    @staticmethod
    async def get_subscription_tiers(db: Session) -> List[SubscriptionTier]:
        """Get all available subscription tiers"""
        return db.query(SubscriptionTier).all()

    @staticmethod
    async def get_user_subscription(
        db: Session,
        user_id: str
    ) -> Optional[UserSubscription]:
        """Get user's current subscription"""
        return db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == 'active'
        ).first()

    @staticmethod
    async def create_subscription(
        db: Session,
        user_id: str,
        tier_id: int,
        stripe_subscription_id: Optional[str] = None
    ) -> UserSubscription:
        """Create a new subscription for a user"""
        try:
            # Check if user already has an active subscription
            existing_sub = await SubscriptionService.get_user_subscription(db, user_id)
            if existing_sub:
                # If there's an existing subscription, mark it as cancelled
                existing_sub.status = 'cancelled'
                db.flush()

            # Create new subscription with incomplete status
            # It will be updated to active by the webhook when payment is confirmed
            subscription = UserSubscription(
                user_id=user_id,
                tier_id=tier_id,
                status='incomplete',
                current_period_start=datetime.now(),
                stripe_subscription_id=stripe_subscription_id
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            return subscription
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create subscription: {str(e)}"
            )

    @staticmethod
    async def calculate_usage_cost(
        db: Session,
        user_id: str,
        pft_used: Decimal
    ) -> Decimal:
        """Calculate cost for PFT usage including any overages"""
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        if not subscription:
            # No subscription - charge base rate for all usage
            return pft_used * Decimal('0.001')
            
        tier = db.query(SubscriptionTier).get(subscription.tier_id)
        if pft_used <= tier.monthly_pft:
            return Decimal('0')  # Within monthly allowance
            
        # Calculate overage
        excess_pft = pft_used - tier.monthly_pft
        return excess_pft * tier.overage_pft_price

    @staticmethod
    def get_example_usage(tier_name: str) -> dict:
        """Get example usage scenarios for a tier"""
        tier = next(t for t in SubscriptionService.DEFAULT_TIERS if t["name"] == tier_name)
        monthly_pft = tier["monthly_pft"]
        
        return {
            "monthly_pft": monthly_pft,
            "examples": {
                "all_input": {
                    "input_tokens": monthly_pft * 1000,  # 1000 tokens per PFT
                    "output_tokens": 0,
                    "storage_mb": 0
                },
                "all_output": {
                    "input_tokens": 0,
                    "output_tokens": monthly_pft * 333,  # 333 tokens per PFT
                    "storage_mb": 0
                },
                "all_storage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "storage_mb": monthly_pft * 50  # 50 MB per PFT
                },
                "mixed_usage": {
                    "input_tokens": monthly_pft * 400,   # 40% of PFT
                    "output_tokens": monthly_pft * 133,  # 40% of PFT
                    "storage_mb": monthly_pft * 10       # 20% of PFT
                }
            }
        }

subscription_service = SubscriptionService()
