-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create files table (independent of chats)
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    s3_key VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- Create chats table
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id),
    content TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- Create chat_files junction table
CREATE TABLE IF NOT EXISTS chat_files (
    chat_id INTEGER REFERENCES chats(id),
    file_id INTEGER REFERENCES files(id),
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (chat_id, file_id)
);

-- Create subscription_tiers table
CREATE TABLE IF NOT EXISTS subscription_tiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    price_usd FLOAT NOT NULL,
    monthly_pft INTEGER NOT NULL,
    overage_pft_price FLOAT NOT NULL,
    input_token_limit INTEGER NOT NULL DEFAULT 0,
    output_token_limit INTEGER NOT NULL DEFAULT 0,
    storage_limit_gb FLOAT NOT NULL DEFAULT 0.0,
    input_token_overage_price FLOAT NOT NULL DEFAULT 0.0001,
    output_token_overage_price FLOAT NOT NULL DEFAULT 0.0003,
    storage_overage_price_gb FLOAT NOT NULL DEFAULT 0.02,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create user_subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    tier_id INTEGER REFERENCES subscription_tiers(id),
    status VARCHAR(50) NOT NULL,
    stripe_subscription_id VARCHAR(255),
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create monthly_usage_summaries table
CREATE TABLE IF NOT EXISTS monthly_usage_summaries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_input_tokens INTEGER NOT NULL DEFAULT 0,
    total_output_tokens INTEGER NOT NULL DEFAULT 0,
    total_storage_bytes BIGINT NOT NULL DEFAULT 0,
    total_storage_gb FLOAT NOT NULL DEFAULT 0.0,
    total_pft FLOAT NOT NULL DEFAULT 0.0,
    input_pft FLOAT NOT NULL DEFAULT 0.0,
    output_pft FLOAT NOT NULL DEFAULT 0.0,
    storage_pft FLOAT NOT NULL DEFAULT 0.0,
    base_cost_usd FLOAT NOT NULL DEFAULT 0.0,
    overage_cost_usd FLOAT NOT NULL DEFAULT 0.0,
    total_cost FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, year, month)
);

-- Create usage_records table
CREATE TABLE IF NOT EXISTS usage_records (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    chat_id INTEGER REFERENCES chats(id),
    message_id INTEGER REFERENCES messages(id),
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    storage_bytes BIGINT DEFAULT 0,
    pft_used FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_files_chat_id ON chat_files(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_files_file_id ON chat_files(file_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_monthly_usage_user_date ON monthly_usage_summaries(user_id, year, month);
CREATE INDEX IF NOT EXISTS idx_usage_records_user_id ON usage_records(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_chat_id ON usage_records(chat_id);

-- Insert default free tier
INSERT INTO subscription_tiers (name, price_usd, monthly_pft, overage_pft_price)
VALUES ('Free', 0.0, 1000, 0.001)
ON CONFLICT DO NOTHING;
