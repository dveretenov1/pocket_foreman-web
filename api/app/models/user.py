from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    chats = relationship("Chat", back_populates="user")
    files = relationship("File", back_populates="user")
    subscriptions = relationship("UserSubscription", back_populates="user")
    usage_records = relationship("UsageRecord", back_populates="user")
    monthly_summaries = relationship("MonthlyUsageSummary", back_populates="user")
