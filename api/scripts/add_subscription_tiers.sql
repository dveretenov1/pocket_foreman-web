INSERT INTO subscription_tiers (
    name,
    price_usd,
    monthly_pft,
    overage_pft_price,
    input_token_limit,
    output_token_limit,
    storage_limit_gb,
    input_token_overage_price,
    output_token_overage_price,
    storage_overage_price_gb
) VALUES 
('Basic', 5.00, 5000, 0.0012, 0, 0, 0, 0.0001, 0.0003, 0.02),
('Pro', 20.00, 22000, 0.0011, 0, 0, 0, 0.0001, 0.0003, 0.02),
('Enterprise', 40.00, 48000, 0.001, 0, 0, 0, 0.0001, 0.0003, 0.02);
