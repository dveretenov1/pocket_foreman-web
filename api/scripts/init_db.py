import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.models.file import File
from app.models.subscription import SubscriptionTier, UserSubscription, UsageRecord, MonthlyUsageSummary
from app.services.billing.subscription import subscription_service

import asyncio

async def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

    # Initialize subscription tiers
    try:
        db = SessionLocal()
        await subscription_service.initialize_tiers(db)
        print("Subscription tiers initialized successfully")
        db.close()
    except Exception as e:
        print(f"Error initializing subscription tiers: {str(e)}")

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db())
    print("Database initialization complete")
