"""
BTC price simulator module with real-time price feed and probability calculation.
"""
import time
import numpy as np
import requests
from scipy.special import expit
from collections import deque
from typing import Dict, Any, Optional
import random


class BTCPriceFeed:
    """Connects to real BTC price data and maintains price history."""
    
    def __init__(self, price_api_url: str = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"):
        """
        Initialize the BTC price feed.
        
        Args:
            price_api_url: URL for the BTC price API
        """
        self.price_api_url = price_api_url
        
        # Rate limiting parameters
        self.last_api_call = 0
        self.min_call_interval = 60  # Minimum seconds between API calls to avoid rate limiting
        self.backoff_time = 0  # Current backoff time if rate limited
        self.consecutive_failures = 0  # Count consecutive API failures
        
        # Get initial price
        self.price = self._fetch_current_price()
        
        # Historical price storage
        self.price_history = deque(maxlen=100)
        self.price_history.append((time.time(), self.price))
        
        # Calculate historical volatility from recent price history
        self.volatility = 0.03  # Default value, will be updated as more data comes in
    
    def _fetch_current_price(self) -> float:
        """
        Fetch the current BTC price from the API with rate limit handling.
        
        Returns:
            Current BTC price in USD
        """
        current_time = time.time()
        
        # Check if we need to respect rate limiting
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_call_interval:
            # If we called the API recently, use the last known price
            if hasattr(self, 'price') and self.price:
                # Small random noise to simulate price movement
                noise = random.uniform(-0.001, 0.001) * self.price
                return self.price * (1 + noise)
            return 80000  # Default fallback price
        
        # Check if we're in backoff mode
        if self.backoff_time > 0 and current_time - self.last_api_call < self.backoff_time:
            if hasattr(self, 'price') and self.price:
                # Add some reasonable noise to the last price
                noise = random.uniform(-0.002, 0.002) * self.price
                return self.price * (1 + noise)
            return 80000  # Default fallback price
        
        # Try to call the API
        try:
            response = requests.get(self.price_api_url, timeout=5)
            self.last_api_call = current_time
            
            # Handle rate limiting responses
            if response.status_code == 429:
                self._handle_rate_limit()
                return self._use_fallback_price()
            
            response.raise_for_status()
            data = response.json()
            price = float(data['bitcoin']['usd'])
            
            # Reset backoff parameters on success
            self.consecutive_failures = 0
            self.backoff_time = 0
            
            return price
            
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Error fetching BTC price: {e}")
            self._handle_rate_limit()
            return self._use_fallback_price()
    
    def _handle_rate_limit(self):
        """Handle rate limiting by implementing exponential backoff."""
        self.consecutive_failures += 1
        
        # Exponential backoff: 1min, 2min, 4min, 8min, etc. up to 30min max
        backoff_seconds = min(30 * 60, self.min_call_interval * (2 ** (self.consecutive_failures - 1)))
        self.backoff_time = backoff_seconds
        
        print(f"Rate limited by CoinGecko API. Backing off for {backoff_seconds/60:.1f} minutes.")
        print("Using simulated price updates until then.")
    
    def _use_fallback_price(self) -> float:
        """Generate a reasonable fallback price when API is unavailable."""
        if hasattr(self, 'price') and self.price and self.price > 0:
            # Generate a random walk based on historical volatility
            vol_factor = self.volatility / np.sqrt(24)  # Convert to hourly volatility
            random_change = random.normalvariate(0, vol_factor) * self.price
            
            # Limit the change to be reasonable (max 0.5% per call)
            capped_change = max(min(random_change, self.price * 0.005), self.price * -0.005)
            
            # Ensure the price remains positive and reasonable
            new_price = max(self.price + capped_change, self.price * 0.99)  # Never drop more than 1% at once
            
            # Sanity check - ensure price is within reasonable bounds (between $10k and $200k)
            return max(min(new_price, 200000), 10000)
        
        # If we have no valid price history, use a reasonable default
        return 80000  # Default fallback price
    
    def update_price(self) -> float:
        """
        Update the current BTC price from the API.
        
        Returns:
            Current BTC price
        """
        # Update the price from the API or cache
        new_price = self._fetch_current_price()
        
        # Validate the new price
        if new_price <= 0 or not isinstance(new_price, (int, float)) or new_price > 500000:
            print(f"Warning: Received invalid price {new_price}. Using previous price or default.")
            if hasattr(self, 'price') and self.price > 0:
                # Keep using the previous valid price
                return self.price
            else:
                # Use a default value
                self.price = 80000
                return self.price
        
        # Only update internal price state if the price actually changed
        # This prevents price history from being flooded with duplicate entries
        if new_price != self.price:
            self.price = new_price
            
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


class ProbabilityCalculator:
    """Calculates the probability of BTC reaching a target price within a timeframe."""
    
    def __init__(self, target_price: float = 100000, timeframe_hours: int = 24, sensitivity: float = 0.1):
        """
        Initialize the probability calculator.
        
        Args:
            target_price: Price target to predict
            timeframe_hours: Timeframe for prediction in hours
            sensitivity: Sensitivity parameter for logistic function
        """
        self.target_price = target_price
        self.timeframe_hours = timeframe_hours
        self.sensitivity = sensitivity
        
        # Setup time tracking
        self.start_time = time.time()
        self.remaining_hours = timeframe_hours
    
    def update_remaining_time(self):
        """Update the remaining time until expiry."""
        current_time = time.time()
        elapsed_hours = (current_time - self.start_time) / 3600
        self.remaining_hours = max(0, self.timeframe_hours - elapsed_hours)
    
    def calculate_probability(self, current_price: float, volatility: float) -> float:
        """
        Calculate the probability of reaching the target price.
        Uses a logistic function based on current price, target, time remaining, and volatility.
        
        Args:
            current_price: Current BTC price
            volatility: Current estimated volatility
            
        Returns:
            Probability (0-1) of reaching the target price
        """
        # Update remaining time
        self.update_remaining_time()
        
        # Input validation
        if not isinstance(current_price, (int, float)) or current_price <= 0:
            print(f"Warning: Invalid price value {current_price}, using fallback price")
            current_price = 80000  # Use a reasonable fallback price
            
        if not isinstance(volatility, (int, float)) or volatility <= 0:
            print(f"Warning: Invalid volatility value {volatility}, using fallback volatility")
            volatility = 0.03  # Use a reasonable fallback volatility
        
        # Enforce reasonable bounds on inputs
        current_price = max(min(current_price, 500000), 1000)  # Between $1k and $500k
        volatility = max(min(volatility, 0.5), 0.01)  # Between 1% and 50%
        
        # Already reached target
        if current_price >= self.target_price:
            return 1.0
            
        # No time left
        if self.remaining_hours <= 0:
            return 0.0
        
        # Calculate distance to target as percentage
        distance_pct = (self.target_price - current_price) / current_price
        
        # Calculate time factor (less time makes target harder to reach)
        time_factor = self.remaining_hours / self.timeframe_hours
        
        # Calculate volatility factor (higher volatility increases probability)
        vol_factor = volatility * np.sqrt(self.remaining_hours)
        
        # Logistic function parameter
        z = -distance_pct / (vol_factor * self.sensitivity) + time_factor
        
        # Calculate probability using logistic function
        probability = expit(z)
        
        # Final sanity check
        if not 0 <= probability <= 1:
            print(f"Warning: Calculated probability {probability} is out of bounds, clamping")
            probability = max(min(probability, 1.0), 0.0)
        
        return probability


class BTCSimulator:
    """Combines the price feed and probability calculator to provide a coherent interface."""
    
    def __init__(self, initial_price: Optional[float] = None, target_price: float = 100000, 
                 timeframe_hours: int = 24, sensitivity: float = 0.1,
                 price_api_url: str = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"):
        """
        Initialize the BTC simulator with price feed and probability calculator.
        
        Args:
            initial_price: Starting BTC price (if None, fetches from API)
            target_price: Price target to predict
            timeframe_hours: Timeframe for prediction in hours
            sensitivity: Sensitivity parameter for logistic function
            price_api_url: URL for the BTC price API
        """
        # Initialize price feed
        self.price_feed = BTCPriceFeed(price_api_url=price_api_url)
        
        # Initialize probability calculator
        self.probability_calculator = ProbabilityCalculator(
            target_price=target_price,
            timeframe_hours=timeframe_hours,
            sensitivity=sensitivity
        )
    
    def update_price(self, dt: float = 0.0) -> float:
        """
        Update the current BTC price from the API and update remaining time.
        
        Args:
            dt: Time step in hours (not used, kept for backward compatibility)
            
        Returns:
            Current BTC price
        """
        return self.price_feed.update_price()
    
    def calculate_probability(self) -> float:
        """
        Calculate the probability of reaching the target price.
        
        Returns:
            Probability of reaching the target price
        """
        current_price = self.price_feed.get_current_price()
        volatility = self.price_feed.get_volatility()
        
        return self.probability_calculator.calculate_probability(current_price, volatility)
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state of the BTC price and prediction.
        
        Returns:
            Dictionary with current state information
        """
        try:
            # Ensure we have the latest price
            self.update_price()
            
            # Get latest values
            current_price = self.price_feed.get_current_price()
            volatility = self.price_feed.get_volatility()
            
            # Validate price and volatility
            if current_price <= 0 or not isinstance(current_price, (int, float)):
                print(f"Error: Invalid price detected ({current_price}). Resetting to default.")
                current_price = 80000  # Reset to a reasonable default
                # Also reset the price feed's internal price
                self.price_feed.price = current_price
            
            if volatility <= 0 or not isinstance(volatility, (int, float)):
                print(f"Error: Invalid volatility detected ({volatility}). Resetting to default.")
                volatility = 0.03  # Reset to a reasonable default
                self.price_feed.volatility = volatility
            
            # Calculate probability with validated values
            probability = self.probability_calculator.calculate_probability(current_price, volatility)
            
            return {
                "price": current_price,
                "target_price": self.probability_calculator.target_price,
                "remaining_hours": self.probability_calculator.remaining_hours,
                "probability": probability,
                "time": time.time(),
                "volatility": volatility
            }
        except Exception as e:
            # Fallback in case of any error
            print(f"Error getting current state: {e}. Using fallback values.")
            return {
                "price": 80000,
                "target_price": self.probability_calculator.target_price,
                "remaining_hours": self.probability_calculator.remaining_hours,
                "probability": 0.5,
                "time": time.time(),
                "volatility": 0.03
            }
    
    @property
    def price(self) -> float:
        """Get the current BTC price."""
        return self.price_feed.get_current_price()
    
    @property
    def target_price(self) -> float:
        """Get the target price."""
        return self.probability_calculator.target_price
    
    @property
    def remaining_hours(self) -> float:
        """Get the remaining hours."""
        self.probability_calculator.update_remaining_time()
        return self.probability_calculator.remaining_hours 