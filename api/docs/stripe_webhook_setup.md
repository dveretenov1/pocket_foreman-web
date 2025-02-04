# Setting Up Stripe Webhooks for Local Development

To test Stripe webhooks locally, you'll need to use the Stripe CLI which creates a secure tunnel to your local server. Here's how to set it up:

1. Install the Stripe CLI:
   ```bash
   # On Linux
   curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
   echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
   sudo apt update
   sudo apt install stripe

   # On macOS with Homebrew
   brew install stripe/stripe-cli/stripe
   ```

2. Login to your Stripe account:
   ```bash
   stripe login
   ```

3. Start the webhook forwarding:
   ```bash
   # Forward events to your local server
   stripe listen --forward-to localhost:8000/webhook/stripe
   ```

4. The Stripe CLI will display a webhook signing secret. Add this to your `.env` file:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx
   ```

5. Keep the `stripe listen` command running while testing webhooks locally.

## Production Setup

For production, update your `.env` file with your production API URL:
```
API_URL=https://your-production-domain.com
```

Then run the webhook setup script:
```bash
cd api
source venv/bin/activate
./scripts/setup_stripe_webhook.py
```

This will create a webhook endpoint in your Stripe dashboard pointing to your production URL.

## Verifying Webhook Configuration

To verify your webhook configuration:
```bash
cd api
source venv/bin/activate
./scripts/check_stripe.py
```

This will show all configured webhook endpoints and their status.
