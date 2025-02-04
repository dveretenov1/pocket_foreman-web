from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class SubscriptionTier(BaseModel):
    id: int
    name: str
    price_usd: Decimal
    monthly_pft: int
    overage_pft_price: Decimal

    class Config:
        from_attributes = True

class SubscriptionCreate(BaseModel):
    tier_id: int
    payment_method_id: Optional[str] = None

class SubscriptionResponse(BaseModel):
    subscription: dict
    tier: SubscriptionTier
    client_secret: Optional[str] = None

class MonthlyUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    storage_bytes: int
    total_pft: float
    cost_usd: float
    base_cost_usd: float
    overage_cost_usd: float
    year: int
    month: int

class UsageResponse(BaseModel):
    input_tokens: int
    output_tokens: int
    storage_bytes: int
    total_pft: float
    cost_usd: float
    base_cost_usd: float
    overage_cost_usd: float

class AdminUsageSummary(BaseModel):
    total_users: int
    total_pft: float
    total_cost_usd: float
    average_pft_per_user: float
    average_cost_per_user: float
