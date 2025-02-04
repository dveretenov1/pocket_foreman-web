# api/app/services/billing/token_conversion.py
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class TokenConversionService:
    """
    Handles conversion of resource usage to PocketForeman Tokens (PFT)
    
    Base rate:
    - 1 PFT = $0.1
    
    Conversion rates:
    - Input tokens: 1 token = 1 PFT
    - Output tokens: 1 token = 3 PFT (3x more expensive than input)
    - Storage: 10 GB = 1 PFT
    """
    
    def __init__(self):
        logger.info("Initializing TokenConversionService")
        self.PFT_TO_USD = 0.1  # 1 PFT = $0.1
        
        # Resource to PFT conversion rates
        self.CONVERSION_RATES = {
            'input_tokens': 1.0,    # 1 input token = 1 PFT
            'output_tokens': 3.0,   # 1 output token = 3 PFT
            'storage_gb': 0.1       # 0.1 GB = 1 PFT
        }
    
    def calculate_pft(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        storage_bytes: int = 0
    ) -> Dict[str, float]:
        """Calculate PocketForeman Tokens for given resource usage"""
        try:
            # Convert all inputs to float
            input_val = float(input_tokens)
            output_val = float(output_tokens)
            storage_val = float(storage_bytes)
            
            # Calculate PFT for each resource type
            input_pft = input_val * self.CONVERSION_RATES['input_tokens']
            output_pft = output_val * self.CONVERSION_RATES['output_tokens']
            
            # Convert bytes to GB then calculate storage PFT
            storage_gb = storage_val / (1024 * 1024 * 1024)  # Convert bytes to GB
            storage_pft = storage_gb * self.CONVERSION_RATES['storage_gb']
            
            # Calculate total PFT
            total_pft = input_pft + output_pft + storage_pft
            
            # Calculate base USD cost
            base_cost_usd = total_pft * self.PFT_TO_USD
            
            return {
                'input_pft': round(input_pft, 2),
                'output_pft': round(output_pft, 2),
                'storage_pft': round(storage_pft, 2),
                'total_pft': round(total_pft, 2),
                'base_cost_usd': round(base_cost_usd, 2),
                'overage_cost_usd': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error in PFT calculation: {str(e)}")
            return {
                'input_pft': 0.0,
                'output_pft': 0.0,
                'storage_pft': 0.0,
                'total_pft': 0.0,
                'base_cost_usd': 0.0,
                'overage_cost_usd': 0.0
            }

# Create singleton instance
token_conversion = TokenConversionService()