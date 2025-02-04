import os
import sys
import stripe
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.billing.subscription import SubscriptionService

def setup_stripe_products():
    # Get Stripe API key from environment
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        print("Error: STRIPE_SECRET_KEY not found in environment variables")
        return

    # Get subscription tiers
    tiers = SubscriptionService.DEFAULT_TIERS

    price_ids = {}
    
    for tier in tiers:
        if tier['name'] == 'Free':
            continue  # Skip free tier as it doesn't need a Stripe product
            
        try:
            # Create or get product
            products = stripe.Product.list(active=True)
            product = next(
                (p for p in products.data if p.name == f"Pocket Foreman {tier['name']}"),
                None
            )
            
            if not product:
                product = stripe.Product.create(
                    name=f"Pocket Foreman {tier['name']}",
                    description=f"{tier['monthly_pft']} PFT monthly allocation"
                )
                print(f"Created product: {product.name}")

            # Create or get price
            prices = stripe.Price.list(product=product.id, active=True)
            price = next(
                (p for p in prices.data if p.unit_amount == int(Decimal(tier['price_usd']) * 100)),
                None
            )
            
            if not price:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(Decimal(tier['price_usd']) * 100),
                    currency='usd',
                    recurring={
                        'interval': 'month'
                    }
                )
                print(f"Created price for {tier['name']}: ${tier['price_usd']}/month")

            # Store price ID
            price_ids[tier['name'].lower()] = price.id
            
        except stripe.error.StripeError as e:
            print(f"Error setting up {tier['name']} tier: {str(e)}")
            continue

    # Print environment variable settings
    print("\nAdd these lines to your .env file:")
    for name, price_id in price_ids.items():
        print(f"STRIPE_PRICE_ID_{name.upper()}={price_id}")

if __name__ == "__main__":
    setup_stripe_products()
