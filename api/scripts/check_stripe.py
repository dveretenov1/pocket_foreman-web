import os
import sys
import stripe
from decimal import Decimal
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import get_settings

def check_stripe_configuration():
    # Get settings which includes Stripe key
    settings = get_settings()
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if not stripe.api_key:
        print("Error: STRIPE_SECRET_KEY not found")
        return

    print("\n=== Stripe Configuration Check ===\n")

    try:
        # List all products
        print("Products:")
        print("---------")
        products = stripe.Product.list(active=True)
        for product in products.data:
            print(f"Product: {product.name} (ID: {product.id})")
            
            # Get prices for this product
            prices = stripe.Price.list(product=product.id, active=True)
            for price in prices.data:
                amount = Decimal(price.unit_amount) / 100  # Convert cents to dollars
                print(f"  - Price: ${amount} {price.currency.upper()} (ID: {price.id})")
                if price.recurring:
                    print(f"    Recurring: {price.recurring.interval}")
            print()

        # Check webhook endpoints
        print("\nWebhook Endpoints:")
        print("----------------")
        webhooks = stripe.WebhookEndpoint.list()
        if not webhooks.data:
            print("No webhook endpoints configured!")
            print("\nTo set up webhooks for local development:")
            print("1. Install Stripe CLI (see api/docs/stripe_webhook_setup.md)")
            print("2. Run: stripe login")
            print("3. Run: stripe listen --forward-to localhost:8000/webhook/stripe")
            print("\nFor production:")
            print("1. Set API_URL in .env")
            print("2. Run: ./scripts/setup_stripe_webhook.py")
        else:
            for webhook in webhooks.data:
                print(f"\nWebhook Details:")
                print(f"  URL: {webhook.url}")
                print(f"  Status: {webhook.status}")
                print(f"  Events: {', '.join(webhook.enabled_events)}")
                print(f"  Created: {datetime.fromtimestamp(webhook.created).strftime('%Y-%m-%d %H:%M:%S')}")
                if webhook.status != "enabled":
                    print(f"  WARNING: Webhook is not enabled!")
                if "localhost" in webhook.url or "127.0.0.1" in webhook.url:
                    print("  WARNING: Using localhost URL - use Stripe CLI for local development")

    except stripe.error.StripeError as e:
        print(f"Stripe Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_stripe_configuration()
