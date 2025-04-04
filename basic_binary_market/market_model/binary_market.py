"""
Binary market model for BTC prediction markets.
"""
import time
import math  # Add math import for isclose
from typing import Dict, List, Optional, Tuple

from basic_binary_market.market_model.order import Order


class BinaryMarket:
    """
    Simulates a binary (YES/NO) prediction market.
    """
    
    def __init__(self, expiry_time: float = None):
        """
        Initialize a binary market.
        
        Args:
            expiry_time: When the market resolves in unix timestamp.
                         If None, defaults to 24 hours from now.
        """
        self.question = "Will BTC reach $100,000 in 24 hours?"
        self.expiry_time = expiry_time or (time.time() + 24 * 60 * 60)
        
        # Order books separated by option (YES/NO) and side (BUY/SELL)
        # We use sorted lists for efficient order matching and book maintenance
        self.order_books = {
            "YES": {"BUY": [], "SELL": []},
            "NO": {"BUY": [], "SELL": []}
        }
        
        self.executed_trades = []
        self.order_id_counter = 1
        self.current_time = time.time()
        self.is_resolved = False
        self.resolution = None  # Will be 'YES' or 'NO' when resolved
        self.true_probability = 0.5  # Initial true probability
        
    def get_order_id(self) -> str:
        """Generate a unique order ID."""
        order_id = f"order_{self.order_id_counter}"
        self.order_id_counter += 1
        return order_id

    def place_limit_order(self, side: str, option: str, price: float, size: float, user_id: str) -> str:
        """
        Place a new limit order in the market.
        
        Args:
            side: 'BUY' or 'SELL'
            option: 'YES' or 'NO'
            price: Price between 0 and 1
            size: Size of the order
            user_id: ID of the user placing the order
            
        Returns:
            Order ID
        """
        self._validate_order_params(side, option, price, size)
            
        # Create new order
        order_id = self.get_order_id()
        timestamp = time.time()
        order = Order(order_id, side, option, price, size, timestamp, user_id)
        
        # Check for immediate execution
        remaining_order = self._match_order(order)
        
        # If order wasn't fully executed, add remaining to book
        if remaining_order and remaining_order.size > 0:
            # Check if we can merge with an existing order at the same price
            merged = False
            if self._is_merge_enabled():
                # Try to merge with existing orders at same price
                existing_orders = self.order_books[option][side]
                for existing in existing_orders:
                    if (math.isclose(existing.price, remaining_order.price, abs_tol=1e-9) and 
                        existing.user_id == remaining_order.user_id):
                        # Merge with existing order at same price
                        existing.size += remaining_order.size
                        merged = True
                        break
            
            # If not merged, add as a new order
            if not merged:
                self._add_to_order_book(remaining_order)
            
        return order_id
    
    def place_market_order(self, side: str, option: str, size: float, user_id: str) -> Dict:
        """
        Place a market order that will execute immediately against the order book.
        Market orders will attempt to fill the entire requested size by matching at
        progressively worse price levels if necessary, rather than leaving the order
        partially unfilled.
        
        Args:
            side: 'BUY' or 'SELL'
            option: 'YES' or 'NO'
            size: Size of the order
            user_id: ID of the user placing the order
            
        Returns:
            Dictionary with execution details
        """
        if side not in ["BUY", "SELL"]:
            raise ValueError("Side must be 'BUY' or 'SELL'")
            
        if option not in ["YES", "NO"]:
            raise ValueError("Option must be 'YES' or 'NO'")
            
        if size <= 0:
            raise ValueError("Size must be positive")
        
        # For market orders, we use a price that will guarantee execution at any price
        # (1.0 for BUY, 0.0 for SELL)
        price = 1.0 if side == "BUY" else 0.0
        
        # Create order
        order_id = self.get_order_id()
        timestamp = time.time()
        order = Order(order_id, side, option, price, size, timestamp, user_id)
        
        # Execute against order book - market orders will be matched at progressively
        # worse prices until fully filled or the book is empty
        remaining_order = self._match_order(order)
        
        # Market orders don't get added to the book if not fully filled
        fills = []
        for trade in self.executed_trades:
            if trade.get("taker_order_id") == order_id:
                fills.append({
                    "price": trade["price"],
                    "size": trade["size"],
                    "option": option
                })
        
        filled_size = size - (remaining_order.size if remaining_order else 0)
        remaining_size = remaining_order.size if remaining_order else 0
        
        # Add warning if market order wasn't fully filled
        result = {
            "order_id": order_id,
            "filled_size": filled_size,
            "fills": fills,
            "remaining_size": remaining_size
        }
        
        if remaining_size > 0:
            result["warning"] = "Market order could not be fully filled due to insufficient liquidity"
            
        return result
    
    def _validate_order_params(self, side: str, option: str, price: float, size: float):
        """Validate order parameters."""
        if self.is_resolved:
            raise ValueError("Market is already resolved")
            
        if side not in ["BUY", "SELL"]:
            raise ValueError("Side must be 'BUY' or 'SELL'")
            
        if option not in ["YES", "NO"]:
            raise ValueError("Option must be 'YES' or 'NO'")
            
        if not 0 <= price <= 1:
            raise ValueError("Price must be between 0 and 1")
            
        if size <= 0:
            raise ValueError("Size must be positive")
    
    def _add_to_order_book(self, order: Order):
        """
        Add an order to the appropriate order book.
        
        This method sorts orders for efficient matching:
        - BUY orders: higher prices first (descending), then earlier timestamps
        - SELL orders: lower prices first (ascending), then earlier timestamps
        """
        # Double-check if this order would match against existing orders first
        # This is a failsafe in case the matching logic missed something
        opposing_side = "SELL" if order.side == "BUY" else "BUY"
        opposing_orders = self.order_books[order.option][opposing_side]
        
        potential_match = False
        if opposing_orders:
            # Price matching logic should be the same as in _match_order
            if order.option == "YES":
                # For YES market:
                if order.side == "BUY":
                    # BUY YES matches if buy_price >= sell_price
                    potential_match = math.isclose(order.price, opposing_orders[0].price, abs_tol=1e-9) or order.price > opposing_orders[0].price
                else:  # order.side == "SELL"
                    # SELL YES matches if sell_price <= buy_price
                    potential_match = math.isclose(order.price, opposing_orders[0].price, abs_tol=1e-9) or order.price < opposing_orders[0].price
            else:  # order.option == "NO"
                # For NO market:
                if order.side == "BUY":
                    potential_match = math.isclose(order.price, opposing_orders[0].price, abs_tol=1e-9) or order.price > opposing_orders[0].price
                else:  # order.side == "SELL"
                    potential_match = math.isclose(order.price, opposing_orders[0].price, abs_tol=1e-9) or order.price < opposing_orders[0].price
                    
            if potential_match:
                # Try matching again to be safe
                remaining = self._match_order(order)
                if remaining is None or remaining.size <= 0:
                    return
                elif remaining.size < order.size:
                    order = remaining  # Continue with the remaining part
        
        # Now add to order book
        self.order_books[order.option][order.side].append(order)
        
        # Sort the order book appropriately
        # For BUY orders: higher prices first (descending)
        # For SELL orders: lower prices first (ascending)
        self.order_books[order.option][order.side].sort(
            key=lambda o: (-o.price if o.side == "BUY" else o.price, o.timestamp)
        )

    def _match_order(self, order: Order) -> Optional[Order]:
        """
        Match an order against the order book.
        
        This is the core order matching algorithm that maintains price-time priority.
        For market orders, it tries to match the entire order by moving to progressively
        worse price levels if needed.
        
        Args:
            order: The order to match
            
        Returns:
            Remaining order if not fully matched, None otherwise
        """
        option = order.option
        side = order.side
        
        # Determine opposing side
        opposing_side = "SELL" if side == "BUY" else "BUY"
        
        # Get the opposing order book
        opposing_orders = self.order_books[option][opposing_side]
        
        # No matching orders
        if not opposing_orders:
            return order
        
        # Process matches while there are matching orders and remaining size
        remaining_size = order.size
        executed_size = 0
        
        i = 0
        while i < len(opposing_orders) and remaining_size > 0:
            opposing_order = opposing_orders[i]
            
            # Price matching logic for YES and NO markets with reliable float comparison
            price_matches = False
            
            if option == "YES":
                # For YES market:
                if side == "BUY":
                    # BUY YES matches if buy_price >= sell_price
                    price_matches = math.isclose(order.price, opposing_order.price, abs_tol=1e-9) or order.price > opposing_order.price
                else:  # side == "SELL"
                    # SELL YES matches if sell_price <= buy_price
                    price_matches = math.isclose(order.price, opposing_order.price, abs_tol=1e-9) or order.price < opposing_order.price
            else:  # option == "NO"
                # For NO market, same logic
                if side == "BUY":
                    price_matches = math.isclose(order.price, opposing_order.price, abs_tol=1e-9) or order.price > opposing_order.price
                else:  # side == "SELL"
                    price_matches = math.isclose(order.price, opposing_order.price, abs_tol=1e-9) or order.price < opposing_order.price
            
            # Check if price matches
            if price_matches:
                # Calculate execution size
                exec_size = min(remaining_size, opposing_order.size)
                
                # Use the price of the resting order
                exec_price = opposing_order.price
                
                # Record the trade
                trade = {
                    "time": time.time(),
                    "option": option,
                    "price": exec_price,
                    "size": exec_size,
                    "taker_side": side,
                    "taker_user_id": order.user_id,
                    "taker_order_id": order.order_id,
                    "maker_user_id": opposing_order.user_id,
                    "maker_order_id": opposing_order.order_id
                }
                self.executed_trades.append(trade)
                
                # Update sizes
                remaining_size -= exec_size
                opposing_order.size -= exec_size
                executed_size += exec_size
                
                # Remove the opposing order if fully executed
                if opposing_order.size <= 0:
                    opposing_orders.pop(i)
                else:
                    i += 1
            else:
                # No more price matches at current price level
                # For market orders, we should continue to the next price level
                if (side == "BUY" and order.price == 1.0) or (side == "SELL" and order.price == 0.0):
                    i += 1  # Move to next order even if price doesn't match
                else:
                    # For limit orders, stop when price no longer matches
                    break
        
        # If order was fully executed, return None
        if remaining_size <= 0:
            return None
        
        # Otherwise, update the size and return
        order.size = remaining_size
        return order
    
    def get_order_book_summary(self) -> Dict:
        """
        Get a summary of the current order book.
        
        Returns:
            Dictionary with BUY and SELL orders for YES and NO options,
            aggregated by price level.
        """
        summary = {
            "YES": {"BUY": [], "SELL": []},
            "NO": {"BUY": [], "SELL": []}
        }
        
        # Process each order book
        for option in ["YES", "NO"]:
            for side in ["BUY", "SELL"]:
                orders = self.order_books[option][side]
                
                # Group by price level
                price_levels = {}
                order_counts = {}  # Track number of orders at each price
                
                for order in orders:
                    price = order.price
                    if price not in price_levels:
                        price_levels[price] = 0
                        order_counts[price] = 0
                    price_levels[price] += order.size
                    order_counts[price] += 1
                
                # Sort price levels
                sorted_prices = sorted(price_levels.keys(), reverse=(side == "BUY"))
                
                # Add to summary
                for price in sorted_prices:
                    summary[option][side].append({
                        "price": price,
                        "size": price_levels[price],
                        "order_count": order_counts[price],
                        "option": option  # Include the option name
                    })
        
        return summary
    
    def get_mid_price(self, option: str) -> float:
        """
        Get the mid price for a specific option.
        
        Args:
            option: 'YES' or 'NO'
            
        Returns:
            Mid price (average of best bid and ask)
        """
        buy_orders = self.order_books[option]["BUY"]
        sell_orders = self.order_books[option]["SELL"]
        
        if not buy_orders and not sell_orders:
            return 0.5  # Default
        
        best_bid = buy_orders[0].price if buy_orders else 0
        best_ask = sell_orders[0].price if sell_orders else 1
        
        return (best_bid + best_ask) / 2
    
    def update_probability(self, new_prob: float):
        """Update the market's true probability."""
        if not 0 <= new_prob <= 1:
            raise ValueError("Probability must be between 0 and 1")
        self.true_probability = new_prob
    
    def resolve_market(self, outcome: str):
        """Resolve the market with the given outcome."""
        if outcome not in ["YES", "NO"]:
            raise ValueError("Outcome must be 'YES' or 'NO'")
            
        self.is_resolved = True
        self.resolution = outcome 
        
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order by its ID.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            True if order was found and canceled, False otherwise
        """
        # Search for the order in all books
        for option in ["YES", "NO"]:
            for side in ["BUY", "SELL"]:
                book = self.order_books[option][side]
                for i, order in enumerate(book):
                    if order.order_id == order_id:
                        # Found the order, remove it
                        book.pop(i)
                        return True
        
        # Order not found
        return False 

    def _print_order_books_debug(self):
        """Debug print of order books."""
        for option in ["YES", "NO"]:
            print(f"{option} Market:")
            
            # Print SELL orders
            print("  SELL orders:")
            sell_orders = self.order_books[option]["SELL"]
            if sell_orders:
                for order in sell_orders:
                    print(f"    {order.size:.2f} @ {order.price:.3f}")
            else:
                print("    No sell orders")
                
            # Print BUY orders
            print("  BUY orders:")
            buy_orders = self.order_books[option]["BUY"]
            if buy_orders:
                for order in buy_orders:
                    print(f"    {order.size:.2f} @ {order.price:.3f}")
            else:
                print("    No buy orders")

    def _is_merge_enabled(self) -> bool:
        """
        Check if order merging is enabled.
        
        This is a control flag to determine whether orders at the same price
        from the same user should be merged or kept separate. For clarity in
        order tracking, we'll keep them separate by default.
        
        Returns:
            Boolean indicating if merging is enabled (True by default)
        """
        return True  # Merge orders at the same price level from the same user 