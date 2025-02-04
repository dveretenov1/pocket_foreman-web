# app/services/billing/usage.py
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime
from typing import Dict, Any, Optional
from ...models.subscription import (
    UsageRecord, 
    MonthlyUsageSummary,
    UserSubscription,
    SubscriptionTier
)
import logging
from .token_conversion import token_conversion

logger = logging.getLogger(__name__)

class UsageService:
    # Base pricing constants as floats
    BASE_PRICES = {
        "INPUT_TOKEN_PRICE": 0.0001,   # $0.10 per 1K input tokens
        "OUTPUT_TOKEN_PRICE": 0.0003,   # $0.30 per 1K output tokens
        "STORAGE_PRICE_GB": 0.02       # $0.02 per GB per month
    }

    @staticmethod
    async def record_usage(
        db: Session,
        user_id: str,
        chat_id: int,
        message_id: int,
        input_tokens: int,
        output_tokens: int,
        storage_bytes: int = 0
    ) -> UsageRecord:
        """Record usage for a message interaction"""
        try:
            # Get or create monthly summary first
            now = datetime.now()
            summary = await UsageService.get_or_create_monthly_summary(
                db, user_id, now.year, now.month
            )

            # Calculate PFT
            pft_info = token_conversion.calculate_pft(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                storage_bytes=storage_bytes
            )
            
            # Create usage record
            usage_record = UsageRecord(
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                storage_bytes=storage_bytes,
                pft_used=float(pft_info['total_pft'])
            )
            db.add(usage_record)
            
            # Update summary totals
            summary.total_input_tokens += input_tokens
            summary.total_output_tokens += output_tokens
            summary.total_storage_bytes += storage_bytes
            
            # Update PFT values
            summary.total_pft += float(pft_info['total_pft'])
            summary.input_pft += float(pft_info['input_pft'])
            summary.output_pft += float(pft_info['output_pft'])
            summary.storage_pft += float(pft_info['storage_pft'])
            
            # Get active subscription and calculate costs
            subscription = db.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == 'active'
            ).first()
            
            if subscription:
                tier = db.query(SubscriptionTier).get(subscription.tier_id)
                if tier:
                    # Calculate costs based on subscription tier
                    monthly_limit = float(tier.monthly_pft)
                    current_total = float(summary.total_pft)
                    overage_pft = max(0.0, current_total - monthly_limit)
                    
                    summary.base_cost_usd = float(tier.price_usd)
                    summary.overage_cost_usd = overage_pft * float(tier.overage_pft_price)
            else:
                # Apply base pricing
                base_cost = (
                    float(pft_info['input_pft']) * UsageService.BASE_PRICES["INPUT_TOKEN_PRICE"] +
                    float(pft_info['output_pft']) * UsageService.BASE_PRICES["OUTPUT_TOKEN_PRICE"] +
                    float(pft_info['storage_pft']) * UsageService.BASE_PRICES["STORAGE_PRICE_GB"]
                )
                
                summary.base_cost_usd = 0.0
                summary.overage_cost_usd = base_cost
            
            db.commit()
            db.refresh(usage_record)
            return usage_record
            
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            db.rollback()
            raise e

    @staticmethod
    async def get_or_create_monthly_summary(
        db: Session,
        user_id: str,
        year: int,
        month: int
    ) -> MonthlyUsageSummary:
        """Get or create monthly usage summary"""
        summary = db.query(MonthlyUsageSummary).filter(
            MonthlyUsageSummary.user_id == user_id,
            MonthlyUsageSummary.year == year,
            MonthlyUsageSummary.month == month
        ).first()
        
        if not summary:
            summary = MonthlyUsageSummary(
                user_id=user_id,
                year=year,
                month=month,
                total_input_tokens=0,
                total_output_tokens=0,
                total_storage_bytes=0,
                total_pft=0.0,
                input_pft=0.0,
                output_pft=0.0,
                storage_pft=0.0,
                base_cost_usd=0.0,
                overage_cost_usd=0.0
            )
            db.add(summary)
            db.commit()
            db.refresh(summary)
        else:
            # Ensure all numeric fields are initialized
            summary.total_pft = float(summary.total_pft or 0)
            summary.input_pft = float(summary.input_pft or 0)
            summary.output_pft = float(summary.output_pft or 0)
            summary.storage_pft = float(summary.storage_pft or 0)
            summary.base_cost_usd = float(summary.base_cost_usd or 0)
            summary.overage_cost_usd = float(summary.overage_cost_usd or 0)
        
        return summary

    @staticmethod
    async def get_monthly_usage(
        db: Session,
        user_id: str,
        year: int,
        month: int
    ) -> Optional[MonthlyUsageSummary]:
        """Get monthly usage summary"""
        summary = db.query(MonthlyUsageSummary).filter(
            MonthlyUsageSummary.user_id == user_id,
            MonthlyUsageSummary.year == year,
            MonthlyUsageSummary.month == month
        ).first()
        
        if summary:
            # Ensure all numeric fields are initialized as floats
            summary.total_pft = float(summary.total_pft or 0)
            summary.input_pft = float(summary.input_pft or 0)
            summary.output_pft = float(summary.output_pft or 0)
            summary.storage_pft = float(summary.storage_pft or 0)
            summary.base_cost_usd = float(summary.base_cost_usd or 0)
            summary.overage_cost_usd = float(summary.overage_cost_usd or 0)
        
        return summary

    @staticmethod
    async def get_current_usage(
        db: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """Get current month's usage statistics"""
        now = datetime.now()
        summary = await UsageService.get_monthly_usage(db, user_id, now.year, now.month)
        
        if not summary:
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "storage_bytes": 0,
                "total_pft": 0.0,
                "cost_usd": 0.0,
                "base_cost_usd": 0.0,
                "overage_cost_usd": 0.0
            }
        
        return {
            "input_tokens": summary.total_input_tokens or 0,
            "output_tokens": summary.total_output_tokens or 0,
            "storage_bytes": summary.total_storage_bytes or 0,
            "total_pft": float(summary.total_pft or 0),
            "cost_usd": float((summary.base_cost_usd or 0) + (summary.overage_cost_usd or 0)),
            "base_cost_usd": float(summary.base_cost_usd or 0),
            "overage_cost_usd": float(summary.overage_cost_usd or 0)
        }

usage_service = UsageService()