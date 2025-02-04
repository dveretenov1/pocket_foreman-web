from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime

class SubscriptionTier(Base):
    __tablename__ = "subscription_tiers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    price_usd = Column(Numeric(10, 2))
    monthly_pft = Column(Integer)  # Monthly PocketForeman Token allocation
    overage_pft_price = Column(Numeric(10, 4))  # Price per PFT for overages

    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="tier")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    tier_id = Column(Integer, ForeignKey("subscription_tiers.id"))
    status = Column(String)  # active, cancelled, past_due
    stripe_subscription_id = Column(String, nullable=True)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    tier = relationship("SubscriptionTier", back_populates="subscriptions")

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))
    message_id = Column(Integer, ForeignKey("messages.id"))
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    storage_bytes = Column(Integer, default=0)
    pft_used = Column(Float, default=0.0)  # Total PFT used for this record
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="usage_records")
    chat = relationship("Chat", back_populates="usage_records")
    message = relationship("Message", back_populates="usage_record")

class MonthlyUsageSummary(Base):
    __tablename__ = "monthly_usage_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    year = Column(Integer)
    month = Column(Integer)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_storage_bytes = Column(Integer, default=0)
    total_pft = Column(Float, default=0.0)
    input_pft = Column(Float, default=0.0)
    output_pft = Column(Float, default=0.0)
    storage_pft = Column(Float, default=0.0)
    base_cost_usd = Column(Float, default=0.0)
    overage_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="monthly_summaries")
