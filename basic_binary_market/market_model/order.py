"""
Order model for the BTC prediction market.
"""
from typing import Dict


class Order:
    """Represents a single order in the market."""
    
    def __init__(self, order_id: str, side: str, option: str, price: float, size: float, 
                 timestamp: float, user_id: str):
        """
        Initialize an order.
        
        Args:
            order_id: Unique identifier for the order
            side: 'BUY' or 'SELL'
            option: 'YES' or 'NO'
            price: Order price (between 0 and 1)
            size: Order size
            timestamp: Time when order was placed
            user_id: ID of the user who placed the order
        """
        self.order_id = order_id
        self.side = side
        self.option = option
        self.price = price
        self.size = size
        self.timestamp = timestamp
        self.user_id = user_id
        
    def __repr__(self):
        return f"Order(id={self.order_id}, side={self.side}, option={self.option}, price={self.price:.3f}, size={self.size:.2f})"
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary for serialization."""
        return {
            "order_id": self.order_id,
            "side": self.side,
            "option": self.option,
            "price": self.price,
            "size": self.size,
            "timestamp": self.timestamp,
            "user_id": self.user_id
        } 