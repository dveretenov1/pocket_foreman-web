from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import user, chat, file, billing, stripe_webhook
from .services.billing.subscription import subscription_service
from .database import engine, Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize subscription tiers
@app.on_event("startup")
async def init_subscription_tiers():
    try:
        from sqlalchemy.orm import Session
        from .database import SessionLocal
        db = SessionLocal()
        await subscription_service.initialize_tiers(db)
        db.close()
    except Exception as e:
        logger.error(f"Error initializing subscription tiers: {str(e)}")

# Include routers
app.include_router(user.router)
app.include_router(chat.router)
app.include_router(file.router)
app.include_router(billing.router)
app.include_router(stripe_webhook.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
