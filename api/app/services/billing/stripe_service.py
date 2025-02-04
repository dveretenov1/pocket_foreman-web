import stripe
from sqlalchemy.orm import Session
from ...models.user import User
from ...models.subscription import UserSubscription, SubscriptionTier
from datetime import datetime
from fastapi import HTTPException
import logging
from typing import Optional, Dict, Any
from ...config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class StripeService:
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Get price IDs from settings
        self.price_ids = {
            "basic": settings.STRIPE_PRICE_ID_BASIC,
            "pro": settings.STRIPE_PRICE_ID_PRO,
            "enterprise": settings.STRIPE_PRICE_ID_ENTERPRISE
        }
        
    async def get_or_create_customer(
        self,
        db: Session,
        user: User,
        payment_method_id: Optional[str] = None
    ) -> str:
        """Get existing or create new Stripe customer"""
        if user.stripe_customer_id:
            return user.stripe_customer_id
            
        try:
            # Create new customer
            customer = self.stripe.Customer.create(
                email=user.email,
                metadata={"user_id": user.id}
            )
            
            # Attach payment method if provided
            if payment_method_id:
                self.stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer.id
                )
                # Set as default payment method
                self.stripe.Customer.modify(
                    customer.id,
                    invoice_settings={
                        "default_payment_method": payment_method_id
                    }
                )
            
            # Update user with customer ID
            user.stripe_customer_id = customer.id
            db.commit()
            
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
            
    async def create_setup_intent(
        self,
        db: Session,
        user: User
    ) -> str:
        """Create a SetupIntent for adding a payment method"""
        try:
            # Get or create customer
            customer_id = await self.get_or_create_customer(db, user)
            
            # Create setup intent
            setup_intent = self.stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                usage='off_session'
            )
            
            return setup_intent.client_secret
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating setup intent: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def create_subscription(
        self,
        db: Session,
        user: User,
        tier_id: int,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new subscription for user"""
        try:
            # Get tier details
            tier = db.query(SubscriptionTier).get(tier_id)
            if not tier:
                raise HTTPException(status_code=404, detail="Tier not found")
                
            # Get or create customer
            customer_id = await self.get_or_create_customer(db, user)
            
            # If payment method provided, attach it
            if payment_method_id:
                try:
                    self.stripe.PaymentMethod.attach(
                        payment_method_id,
                        customer=customer_id
                    )
                    # Set as default payment method
                    self.stripe.Customer.modify(
                        customer_id,
                        invoice_settings={
                            "default_payment_method": payment_method_id
                        }
                    )
                except stripe.error.StripeError as e:
                    logger.error(f"Error attaching payment method: {str(e)}")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid payment method"
                    )
            
            # Get price ID for tier
            price_id = self.price_ids.get(tier.name.lower())
            if not price_id:
                raise HTTPException(
                    status_code=500,
                    detail=f"Price ID not found for tier {tier.name}"
                )
            
            # Create subscription
            subscription = self.stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
                metadata={
                    "user_id": user.id,
                    "tier_id": tier_id
                }
            )
            
            if not subscription.latest_invoice.payment_intent:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create payment intent"
                )
            
            return {
                "subscriptionId": subscription.id,
                "clientSecret": subscription.latest_invoice.payment_intent.client_secret
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
            
    async def cancel_subscription(
        self,
        db: Session,
        user: User
    ):
        """Cancel user's active subscription"""
        try:
            # Get active subscription
            subscription = db.query(UserSubscription).filter(
                UserSubscription.user_id == user.id,
                UserSubscription.status == "active"
            ).first()
            
            if not subscription:
                raise HTTPException(
                    status_code=404,
                    detail="No active subscription found"
                )
            
            # Cancel in Stripe
            if subscription.stripe_subscription_id:
                self.stripe.Subscription.delete(
                    subscription.stripe_subscription_id
                )
            
            # Update local subscription
            subscription.status = "cancelled"
            db.commit()
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
            
    async def get_payment_methods(
        self,
        user: User
    ) -> list:
        """Get user's saved payment methods"""
        try:
            if not user.stripe_customer_id:
                return []
                
            payment_methods = self.stripe.PaymentMethod.list(
                customer=user.stripe_customer_id,
                type="card"
            )
            
            return [{
                "id": pm.id,
                "brand": pm.card.brand,
                "last4": pm.card.last4,
                "exp_month": pm.card.exp_month,
                "exp_year": pm.card.exp_year
            } for pm in payment_methods.data]
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting payment methods: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

stripe_service = StripeService()
