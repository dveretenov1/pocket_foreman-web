from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
from ..database import get_db
from ..models.subscription import UserSubscription, SubscriptionTier
from ..models.user import User
from datetime import datetime
import logging
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

# Initialize Stripe with secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

def handle_subscription_created(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription created event"""
    try:
        subscription_id = subscription_data["id"]
        customer_id = subscription_data["customer"]
        status = subscription_data["status"]
        
        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.error(f"User not found for Stripe customer {customer_id}")
            return
            
        # Get tier from metadata
        tier_id = subscription_data.get("metadata", {}).get("tier_id")
        if not tier_id:
            logger.error(f"No tier_id in metadata for subscription {subscription_id}")
            return
            
        # Create subscription record
        subscription = UserSubscription(
            user_id=user.id,
            tier_id=int(tier_id),
            stripe_subscription_id=subscription_id,
            status=status,
            current_period_end=datetime.fromtimestamp(
                subscription_data["current_period_end"]
            )
        )
        db.add(subscription)
        db.commit()
        logger.info(f"Created subscription {subscription_id} for user {user.id}")
            
    except Exception as e:
        logger.error(f"Error handling subscription creation: {str(e)}")
        db.rollback()

def handle_subscription_updated(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription updated event"""
    try:
        subscription_id = subscription_data["id"]
        status = subscription_data["status"]
        customer_id = subscription_data["customer"]
        
        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.error(f"User not found for Stripe customer {customer_id}")
            return
            
        # Update subscription
        subscription = db.query(UserSubscription).filter(
            UserSubscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            if status == "active":
                subscription.status = status
                subscription.current_period_end = datetime.fromtimestamp(
                    subscription_data["current_period_end"]
                )
            elif status in ["canceled", "unpaid", "incomplete_expired"]:
                subscription.status = "cancelled"
                
            db.commit()
            logger.info(f"Updated subscription {subscription_id} status to {status}")
        else:
            # If subscription not found, might be a new one
            if status == "active":
                handle_subscription_created(subscription_data, db)
            else:
                logger.error(f"Subscription {subscription_id} not found for user {user.id}")
            
    except Exception as e:
        logger.error(f"Error handling subscription update: {str(e)}")
        db.rollback()

def handle_payment_succeeded(payment_data: Dict[str, Any], db: Session):
    """Handle successful payment"""
    try:
        customer_id = payment_data["customer"]
        amount = payment_data["amount"]
        
        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.error(f"User not found for Stripe customer {customer_id}")
            return
            
        logger.info(f"Payment succeeded for user {user.id}: ${amount/100:.2f}")
        
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")

@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    # Get the webhook payload
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        # Handle different event types
        if event.type == "customer.subscription.created":
            handle_subscription_created(event.data.object, db)
            
        elif event.type == "customer.subscription.updated":
            handle_subscription_updated(event.data.object, db)
            
        elif event.type == "customer.subscription.deleted":
            handle_subscription_updated(event.data.object, db)
            
        elif event.type == "payment_intent.succeeded":
            handle_payment_succeeded(event.data.object, db)
            
        elif event.type == "invoice.paid":
            # Update subscription status if needed
            subscription_id = event.data.object.subscription
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                handle_subscription_updated(subscription, db)
                
        elif event.type == "invoice.payment_failed":
            # Handle failed payment
            subscription_id = event.data.object.subscription
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                handle_subscription_updated(subscription, db)
            
        return {"status": "success"}
        
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
