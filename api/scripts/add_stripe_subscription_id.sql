-- Add stripe_subscription_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_subscriptions' 
        AND column_name = 'stripe_subscription_id'
    ) THEN
        ALTER TABLE user_subscriptions 
        ADD COLUMN stripe_subscription_id VARCHAR(255);
    END IF;
END $$;
