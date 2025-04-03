"""
BTC price feed module that connects to real-time BTC price data.
"""
import time
import numpy as np
import requests
from collections import deque
from typing import Dict, Any


class BTCPriceFeed:
    """Connects to real BTC price data and maintains price history."""
    
    def __init__(self, price_api_url: str = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"):
        """
        Initialize the BTC price feed.
        
        Args:
            price_api_url: URL for the BTC price API
        """
        self.price_api_url = price_api_url
        self.price = self._fetch_current_price()
        
        # Historical price storage
        self.price_history = deque(maxlen=100)
        self.price_history.append((time.time(), self.price))
        
        # Calculate historical volatility from recent price history
        self.volatility = 0.03  # Default value, will be updated as more data comes in
    
    def _fetch_current_price(self) -> float:
        """
        Fetch the current BTC price from the API.
        
        Returns:
            Current BTC price in USD
        """
        try:
            response = requests.get(self.price_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return float(data['bitcoin']['usd'])
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Error fetching BTC price: {e}")
            # Return last known price, or a default if we have no history
            if hasattr(self, 'price') and self.price:
                return self.price
            return 80000  # Default fallback price
    
    def update_price(self) -> float:
        """
        Update the current BTC price from the API.
        
        Returns:
            Current BTC price
        """
        # Update the price from the API
        self.price = self._fetch_current_price()
        
        # Add to price history
        current_time = time.time()
        self.price_history.append((current_time, self.price))
        
        # Update volatility estimate if we have enough data points
        if len(self.price_history) >= 10:
            self._update_volatility_estimate()
        
        return self.price
    
    def _update_volatility_estimate(self):
        """Calculate realized volatility from recent price history."""
        # Extract prices and timestamps
        timestamps = []
        prices = []
        
        for timestamp, price in self.price_history:
            timestamps.append(timestamp)
            prices.append(price)
        
        # Calculate log returns
        returns = []
        for i in range(1, len(prices)):
            # Convert to hourly returns
            time_diff_hours = (timestamps[i] - timestamps[i-1]) / 3600
            if time_diff_hours > 0:
                log_return = np.log(prices[i] / prices[i-1]) / np.sqrt(time_diff_hours)
                returns.append(log_return)
        
        # Calculate volatility if we have returns
        if returns:
            # Standard deviation of returns is the volatility estimate
            self.volatility = max(0.01, np.std(returns))  # Ensure minimum volatility
    
    def get_current_price(self) -> float:
        """
        Get the current BTC price.
        
        Returns:
            Current BTC price
        """
        return self.price
    
    def get_volatility(self) -> float:
        """
        Get the current estimated volatility.
        
        Returns:
            Estimated volatility
        """
        return self.volatility
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state of the BTC price feed.
        
        Returns:
            Dictionary with current price information
        """
        # Ensure we have the latest price
        self.update_price()
        
        return {
            "price": self.price,
            "volatility": self.volatility,
            "time": time.time()
        } 