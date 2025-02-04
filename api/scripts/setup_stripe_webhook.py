#!/usr/bin/env python3
import os
import sys
import stripe

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import get_settings

def setup_webhook():
    # Get settings which includes Stripe key
    settings = get_settings()
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if not stripe.api_key:
        print("Error: STRIPE_SECRET_KEY not found")
        return

    try:
        # Construct webhook URL (assuming API runs on localhost:8000 in development)
        base_url = os.getenv('API_URL', 'http://localhost:8000').rstrip('/')
        webhook_url = f"{base_url}/webhook/stripe"
        
        print(f"\nSetting up webhook at: {webhook_url}")

        # List existing webhooks
        existing_webhooks = stripe.WebhookEndpoint.list()
        
        # Check if webhook already exists
        webhook_exists = False
        for webhook in existing_webhooks.data:
            if webhook.url == webhook_url:
                print(f"\nWebhook already exists at {webhook_url}")
                webhook_exists = True
                break

        if not webhook_exists:
            # Create webhook endpoint
            webhook = stripe.WebhookEndpoint.create(
                url=webhook_url,
                enabled_events=[
                    "customer.subscription.created",
                    "customer.subscription.updated",
                    "customer.subscription.deleted",
                    "payment_intent.succeeded",
                    "invoice.paid",
                    "invoice.payment_failed"
                ]
            )
            
            print("\nWebhook endpoint created successfully!")
            print(f"URL: {webhook.url}")
            print(f"Secret: {webhook.secret}")
            print("\nIMPORTANT: Add this webhook secret to your .env file as STRIPE_WEBHOOK_SECRET")
        
        # Verify webhook is listed
        print("\nVerifying webhook configuration...")
        webhooks = stripe.WebhookEndpoint.list()
        found = False
        for webhook in webhooks.data:
            if webhook.url == webhook_url:
                print(f"\nFound webhook:")
                print(f"URL: {webhook.url}")
                print(f"Status: {webhook.status}")
                print(f"Events: {', '.join(webhook.enabled_events)}")
                found = True
                break
        
        if not found:
            print("\nError: Webhook was not found after creation!")

    except stripe.error.StripeError as e:
        print(f"Stripe Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    setup_webhook()
