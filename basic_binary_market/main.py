"""
Main application module for the BTC prediction market.
"""
import argparse
import time
import datetime
import math
import os
from basic_binary_market.market_model import BinaryMarket
from basic_binary_market.simulators import BTCSimulator


class MarketSimulatorApp:
    """Interactive application for the BTC prediction market."""
    
    def __init__(self, target_price: float = 100000, timeframe_hours: int = 24):
        """
        Initialize the application.
        
        Args:
            target_price: Target BTC price to predict
            timeframe_hours: Timeframe for prediction in hours
        """
        # Create market for "Will BTC reach $target_price in timeframe_hours hours?"
        expiry_time = time.time() + timeframe_hours * 60 * 60
        self.market = BinaryMarket(
            expiry_time=expiry_time
        )
        # Update the question to include the target price
        self.market.question = f"Will BTC reach ${target_price:,} in {timeframe_hours} hours?"
        
        # Create BTC price feed and probability calculator
        self.btc_simulator = BTCSimulator(
            target_price=target_price,
            timeframe_hours=timeframe_hours,
            sensitivity=0.15  # Adjust sensitivity for more realistic probabilities
        )
        
        # Display initial BTC price from the API
        initial_state = self.btc_simulator.get_current_state()
        print(f"Current BTC Price: ${initial_state['price']:,.2f}")
        print(f"Target: ${target_price:,.2f}")
        print(f"Probability: {initial_state['probability']:.2%}")
        print(f"Connecting to real-time BTC price feed...\n")
        
        # User ID for the interactive user
        self.user_id = "user"
        
        # Rate limiting for UI updates
        self.last_price_update = time.time()
        self.price_update_interval = 60  # Update price display every 60 seconds
        self.current_state = initial_state
        
        self.running = False
        self.update_thread = None
    
    def start(self):
        """Start the application."""
        # Start market update thread
        self.running = True
        
        # Add some initial liquidity from simulated market makers
        self._add_initial_liquidity()
        
        # Main command loop
        self._command_loop()
    
    def stop(self):
        """Stop the application."""
        self.running = False
    
    def _update_market_probability(self):
        """Update the market's probability based on current BTC price."""
        current_time = time.time()
        
        # Only update the price at certain intervals to avoid rate limiting
        if current_time - self.last_price_update >= self.price_update_interval:
            self.current_state = self.btc_simulator.get_current_state()
            self.last_price_update = current_time
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Price updated: ${self.current_state['price']:,.2f}")
        
        # Update market probability (using current_state, which may be cached)
        self.market.update_probability(self.current_state["probability"])
        
        # Check if market should be resolved
        if self.current_state["price"] >= self.current_state["target_price"]:
            if not self.market.is_resolved:
                print(f"\nBTC has reached the target price of ${self.current_state['target_price']:,.2f}!")
                print("Market is being resolved to YES")
                self.market.resolve_market("YES")
                
        elif self.current_state["remaining_hours"] <= 0:
            if not self.market.is_resolved:
                print(f"\nTime has expired and BTC did not reach the target price of ${self.current_state['target_price']:,.2f}")
                print("Market is being resolved to NO")
                self.market.resolve_market("NO")
    
    def _add_initial_liquidity(self):
        """Add initial liquidity to the market from simulated market makers."""
        # Create a balanced set of orders with clean price levels
        
        # YES market - 2 sell orders and 2 buy orders
        print("Adding initial liquidity - YES market:")
        self.market.place_limit_order("SELL", "YES", 0.70, 10.0, "mm_yes_sell_1")  # Higher sell price
        self.market.place_limit_order("SELL", "YES", 0.60, 15.0, "mm_yes_sell_2")  # Lower sell price
        self.market.place_limit_order("BUY", "YES", 0.40, 15.0, "mm_yes_buy_1")    # Higher buy price
        self.market.place_limit_order("BUY", "YES", 0.30, 10.0, "mm_yes_buy_2")    # Lower buy price
        
        # NO market - 2 sell orders and 2 buy orders
        print("Adding initial liquidity - NO market:")
        self.market.place_limit_order("SELL", "NO", 0.70, 10.0, "mm_no_sell_1")    # Higher sell price
        self.market.place_limit_order("SELL", "NO", 0.60, 15.0, "mm_no_sell_2")    # Lower sell price
        self.market.place_limit_order("BUY", "NO", 0.40, 15.0, "mm_no_buy_1")      # Higher buy price
        self.market.place_limit_order("BUY", "NO", 0.30, 10.0, "mm_no_buy_2")      # Lower buy price
        
        # Set initial probability based on mid prices
        yes_mid_price = (0.40 + 0.60) / 2  # Mid between best bid and ask
        self.market.update_probability(yes_mid_price)
    
    def _print_market_status(self):
        """Print the current market status."""
        # Clear screen
        print("\033c", end="")
        
        # Update probabilities based on latest BTC price
        self._update_market_probability()
        
        # Market information
        btc_state = self.current_state  # Use the cached state, updated periodically
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"========== BTC PREDICTION MARKET ==========")
        print(f"Question: {self.market.question}")
        print(f"Current BTC Price: ${btc_state['price']:,.2f}")
        print(f"Last Updated: {current_time}")
        print(f"Target: ${btc_state['target_price']:,.2f}")
        print(f"Time Remaining: {btc_state['remaining_hours']:.2f} hours")
        print(f"Estimated Volatility: {btc_state['volatility']:.4f}")
        print(f"Probability of Reaching Target: {btc_state['probability']:.2%}")
        
        if self.market.is_resolved:
            print(f"MARKET RESOLVED: {self.market.resolution}")
        
        print()
        
        # Order book
        print("YES Market:")
        self._display_order_book_for_option("YES")
        
        print("\nNO Market:")
        self._display_order_book_for_option("NO")
    
    def _display_order_book_for_option(self, option):
        """Display the order book for a specific option."""
        # Get the order book summary
        order_book = self.market.get_order_book_summary()
        
        # Format sell orders (asks) - display from highest to lowest price
        sells = order_book[option]["SELL"]
        if sells:
            # Reverse the order to display highest price first
            for level in sorted(sells, key=lambda x: x["price"], reverse=True):
                price = level["price"]
                size = level["size"]
                order_count = level.get("order_count", self._count_orders_at_price(option, "SELL", price))
                
                # Format price to avoid rounding issues
                price_str = f"{price:.6f}".rstrip('0').rstrip('.') if price < 1.0 else "1.0"
                
                # Show order count if more than one order at this price
                count_info = f" ({order_count} orders)" if order_count > 1 else ""
                print(f"  SELL {size:8.2f} @ {price_str}{count_info}")
        else:
            print("  No SELL orders")
        
        # Calculate and display the spread
        buys = order_book[option]["BUY"]
        best_bid = buys[0]["price"] if buys else None
        best_ask = min(sell["price"] for sell in sells) if sells else None
        
        if best_bid is not None and best_ask is not None:
            spread = best_ask - best_bid
            spread_percentage = (spread / ((best_bid + best_ask) / 2)) * 100
            print(f"  {'-' * 30}")
            print(f"  SPREAD: {spread:.6f} ({spread_percentage:.2f}%)")
        else:
            print(f"  {'-' * 30}")
            print(f"  SPREAD: N/A (No orders on both sides)")
        
        # Format buy orders (bids) - already displaying from highest to lowest
        if buys:
            for level in buys:
                price = level["price"]
                size = level["size"]
                order_count = level.get("order_count", self._count_orders_at_price(option, "BUY", price))
                
                # Format price to avoid rounding issues
                price_str = f"{price:.6f}".rstrip('0').rstrip('.') if price < 1.0 else "1.0"
                
                # Show order count if more than one order at this price
                count_info = f" ({order_count} orders)" if order_count > 1 else ""
                print(f"  BUY  {size:8.2f} @ {price_str}{count_info}")
        else:
            print("  No BUY orders")
    
    def _get_book_copy(self):
        """Get a deep copy of the current order book state for comparison."""
        book_summary = {}
        for option in ["YES", "NO"]:
            book_summary[option] = {}
            for side in ["BUY", "SELL"]:
                book_summary[option][side] = []
                for order in self.market.order_books[option][side]:
                    book_summary[option][side].append({
                        "size": order.size,
                        "price": order.price,
                        "user_id": order.user_id
                    })
        return book_summary
        
    def _count_orders_at_price(self, option, side, price):
        """Count individual orders at a specific price level."""
        count = 0
        for order in self.market.order_books[option][side]:
            if math.isclose(order.price, price, abs_tol=1e-9):
                count += 1
        return count
    
    def _show_book_comparison(self, before_state):
        """Show a comparison between order books before and after order execution."""
        print("\n===== ORDER BOOK CHANGES =====")
        
        for option in ["YES", "NO"]:
            changes_found = False
            
            # Check for changes in the order book
            for side in ["BUY", "SELL"]:
                # Get current state
                current_orders = self.market.order_books[option][side]
                before_orders = before_state[option][side]
                
                # Check for orders that were removed (fully executed)
                removed_orders = []
                for before_order in before_orders:
                    # Find if this order still exists
                    exists = False
                    for current_order in current_orders:
                        if (math.isclose(current_order.price, before_order["price"], abs_tol=1e-9) and 
                            current_order.user_id == before_order["user_id"] and
                            math.isclose(current_order.size, before_order["size"], abs_tol=1e-9)):
                            exists = True
                            break
                    
                    if not exists:
                        removed_orders.append(before_order)
                
                # Check for new orders or size changes
                new_or_changed = []
                for current_order in current_orders:
                    # Try to find matching order in before state
                    matching_before = None
                    for before_order in before_orders:
                        if (math.isclose(current_order.price, before_order["price"], abs_tol=1e-9) and 
                            current_order.user_id == before_order["user_id"]):
                            matching_before = before_order
                            break
                    
                    if matching_before is None:
                        new_or_changed.append({
                            "type": "new",
                            "order": current_order
                        })
                    elif not math.isclose(current_order.size, matching_before["size"], abs_tol=1e-9):
                        new_or_changed.append({
                            "type": "changed",
                            "order": current_order,
                            "old_size": matching_before["size"]
                        })
                
                # Print removed orders
                if removed_orders:
                    changes_found = True
                    print(f"\n{option} {side} orders removed:")
                    for order in removed_orders:
                        print(f"  {order['size']:.2f} @ {order['price']:.3f} (user: {order['user_id']})")
                
                # Print new or changed orders
                if new_or_changed:
                    changes_found = True
                    print(f"\n{option} {side} orders added or changed:")
                    for item in new_or_changed:
                        if item["type"] == "new":
                            print(f"  + {item['order'].size:.2f} @ {item['order'].price:.3f} (user: {item['order'].user_id})")
                        else:  # changed
                            print(f"  ~ {item['old_size']:.2f} → {item['order'].size:.2f} @ {item['order'].price:.3f} (user: {item['order'].user_id})")
            
            if not changes_found:
                print(f"\n{option} market: No changes")
    
    def _print_order_book(self):
        """Print the current state of the order book."""
        # Get the order book summary
        book = self.market.get_order_book_summary()

        # Print YES market
        print("\nYES Market:")
        self._print_order_book_side(book["YES"]["SELL"], "SELL")
        print("  " + "-" * 45)
        self._print_order_book_side(book["YES"]["BUY"], "BUY")
        
        # Print NO market
        print("\nNO Market:")
        self._print_order_book_side(book["NO"]["SELL"], "SELL")
        print("  " + "-" * 45)
        self._print_order_book_side(book["NO"]["BUY"], "BUY")

    def _print_order_book_side(self, orders, side):
        """Print one side of the order book with order counts."""
        if not orders:
            print(f"  No {side} orders")
            return
        
        # Sort orders to display from highest to lowest price for both sides
        sorted_orders = sorted(orders, key=lambda x: x["price"], reverse=True)
        
        # Print each price level
        for level in sorted_orders:
            price = level["price"]
            size = level["size"]
            order_count = level.get("order_count", self._count_orders_at_price(level["option"], side, price))
            
            # Format price to avoid rounding issues
            price_str = f"{price:.6f}".rstrip('0').rstrip('.') if price < 1.0 else "1.0"
            
            # Show order count if more than one order at this price
            count_info = f" ({order_count} orders)" if order_count > 1 else ""
            print(f"  {side:4} {size:8.2f} @ {price_str}{count_info}")
    
    def get_order_book_summary(self):
        """Get a summary of the order books with additional metadata."""
        summary = self.market.get_order_book_summary()
        
        # Add option field to each level for tracking
        for option in ["YES", "NO"]:
            summary[option]["option"] = option
            
        return summary
    
    def _command_loop(self):
        """Main interactive command loop."""
        print("Welcome to the BTC Prediction Market Simulator!")
        print("Type 'help' for available commands")
        
        while self.running:
            self._print_market_status()
            
            try:
                cmd = input("\nEnter command: ").strip().lower()
                
                if cmd == "quit" or cmd == "exit":
                    self.stop()
                    break
                    
                elif cmd == "help":
                    self._handle_help()
                    
                elif cmd.startswith("limit"):
                    self._handle_limit_order(cmd)
                    
                elif cmd.startswith("market"):
                    self._handle_market_order(cmd)
                    
                elif cmd.startswith("cancel"):
                    self._handle_cancel(cmd)
                    
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                time.sleep(1)
    
    def _handle_help(self):
        """Display help information."""
        print("\nBTC PREDICTION MARKET HELP")
        print("==========================")
        print("\nThis is a simulated binary prediction market for BTC price movements.")
        print("You can place orders in both YES and NO markets.")
        
        print("\nBASIC COMMANDS:")
        print("  help          - Show this help message")
        print("  exit/quit     - Exit the simulator")
        print("  book          - Display the current order book")
        print("  balance       - Show your current balance")
        print("  orders        - Show your active orders")
        print("  cancel <id>   - Cancel an order by ID")
        
        print("\nORDER PLACEMENT:")
        print("  limit <side> <option> <price> <size>")
        print("      - Place a limit order")
        print("      - Example: limit buy yes 0.7 10")
        print("      - This places a buy order for 10 units of YES at a price of 0.7")
        
        print("  market <side> <option> <size>")
        print("      - Place a market order (executes immediately at best available price)")
        print("      - Example: market sell no 5")
        print("      - This sells 5 units of NO at the best available price")
        
        print("\nORDER MATCHING EXPLAINED:")
        print("  * When you place a limit order, it will be matched against existing orders:")
        print("      - BUY orders match with SELL orders at the same or lower price")
        print("      - SELL orders match with BUY orders at the same or higher price")
        print("  * Orders are matched with price-time priority")
        print("      - Better prices are executed first")
        print("      - For orders at the same price, older orders execute first (FIFO)")
        print("  * If your order is only partially executed, the remaining size will be added to the book")
        print("  * In the order book display, orders at the same price are aggregated")
        print("      - The spread shows the difference between best bid and ask prices")
        print("      - Order counts show how many individual orders exist at each price level")
        print("  * The order execution results show exactly how much of your order was executed")
        print("      and how much was added to the book")
        
        print("\nMARKET INFORMATION:")
        print("  * Binary markets have two complementary assets: YES and NO")
        print("  * Prices are between 0 and 1, representing the probability of the event")
        print("  * YES pays 1 if the event happens, 0 otherwise")
        print("  * NO pays 1 if the event doesn't happen, 0 otherwise")
        print("  * The sum of a YES and NO contract at the same strike always equals 1")
        
        print("\nTECHNICAL DETAILS:")
        print("  * Matching Algorithm: Price-Time Priority (FIFO)")
        print("      - Orders are sorted by price, then by time of arrival")
        print("      - This rewards market makers who place orders earlier")
        print("  * Order Book Structure:")
        print("      - Central Limit Order Book (CLOB) model")
        print("      - BUY orders sorted by price (descending)")
        print("      - SELL orders sorted by price (ascending)")
        print("  * Market Resolution:")
        print("      - Automatic resolution based on BTC price reaching target")
        print("      - Binary payout (1 or 0) based on outcome")
        
        input("\nPress Enter to continue...")
    
    def _handle_limit_order(self, cmd):
        """Handle a limit order command."""
        parts = cmd.split()
        if len(parts) != 5:
            print("Invalid limit order format. Example: limit buy yes 0.7 10")
            return
            
        try:
            _, side, option, price, size = parts
            side = side.upper()
            option = option.upper()
            price = float(price)
            size = float(size)
            
            # Store initial state of order book and executed trades for comparison
            initial_book_state = self._get_book_copy()
            initial_trade_count = len(self.market.executed_trades)
            
            # Debug information to help diagnose potential matching issues
            opposing_side = "SELL" if side == "BUY" else "BUY"
            debug_info = [f"Debug info before placing order:"]
            debug_info.append(f"Looking for {opposing_side} {option} orders at price: {price:.6f}")
            matching_orders_found = False
            
            for order in self.market.order_books[option][opposing_side]:
                price_match = False
                if side == "BUY":
                    price_match = math.isclose(order.price, price, abs_tol=1e-9) or order.price < price
                else:  # SELL
                    price_match = math.isclose(order.price, price, abs_tol=1e-9) or order.price > price
                    
                if price_match:
                    debug_info.append(f"  Found matching order: {opposing_side} {order.size:.2f} @ {order.price:.6f} (user: {order.user_id})")
                    matching_orders_found = True
                    
            if not matching_orders_found:
                debug_info.append(f"  No matching {opposing_side} orders found at price {price:.6f}")
            
            # Place the order
            order_id = self.market.place_limit_order(side, option, price, size, self.user_id)
            
            # Get new trades that occurred from this order
            new_trades = self.market.executed_trades[initial_trade_count:]
            
            # Clear the screen for a clean display
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Show the order execution results clearly
            print(f"\n===== ORDER EXECUTION RESULTS =====")
            if new_trades:
                total_executed = sum(trade['size'] for trade in new_trades)
                print(f"Order: {side} {option} {size:.2f} @ {price:.3f}")
                print(f"Executed: {total_executed:.2f} units")
                
                # Show the trades that were executed
                print("\nExecuted trades:")
                for trade in new_trades:
                    print(f"  {trade['taker_side']} {trade['option']} {trade['size']:.2f} @ {trade['price']:.6f}")
                
                if total_executed < size:
                    remaining = size - total_executed
                    print(f"\nRemaining {remaining:.2f} units added to order book")
            else:
                print(f"Order added to book: {side} {option} {size:.2f} @ {price:.3f}")
                print("No immediate execution")
            
            # Show the debug info after clearing the screen
            print("\n===== DEBUG INFO =====")
            for line in debug_info:
                print(line)
            
            # Show comparison of order book before and after
            self._show_book_comparison(initial_book_state)
            
            print("\nCurrent order book:")
            self._print_order_book()
            
        except ValueError as e:
            print(f"Error: {str(e)}")
    
    def _handle_market_order(self, cmd):
        """Handle a market order command."""
        parts = cmd.split()
        if len(parts) != 4:
            print("Invalid market order format. Example: market sell no 5")
            time.sleep(1)
            return
            
        try:
            _, side, option, size = parts
            side = side.upper()
            option = option.upper()
            size = float(size)
            
            result = self.market.place_market_order(side, option, size, self.user_id)
            
            # Display a simple confirmation
            print(f"\nMarket order executed: {result['filled_size']:.2f} of {size:.2f} {side} {option}")
            
            if result['remaining_size'] > 0:
                print(f"Warning: Could not fill entire order - insufficient liquidity")
                
            # Small delay to show the message
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error placing market order: {str(e)}")
            time.sleep(1)
    
    def _handle_cancel(self, cmd):
        """Handle a cancel order command."""
        parts = cmd.split()
        if len(parts) != 2:
            print("Invalid cancel format. Example: cancel order_123")
            time.sleep(1)
            return
            
        try:
            _, order_id = parts
            success = self.market.cancel_order(order_id)
            
            if success:
                print(f"Order {order_id} canceled successfully")
            else:
                print(f"Order {order_id} not found")
                
            time.sleep(1)
            
        except Exception as e:
            print(f"Error canceling order: {str(e)}")
            time.sleep(1)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="BTC Prediction Market Simulator")
    parser.add_argument("--target", type=float, default=100000,
                        help="Target BTC price for prediction (default: $100,000)")
    parser.add_argument("--timeframe", type=int, default=24,
                        help="Timeframe in hours (default: 24)")
    
    args = parser.parse_args()
    
    app = MarketSimulatorApp(target_price=args.target, timeframe_hours=args.timeframe)
    
    try:
        app.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app.stop()


if __name__ == "__main__":
    main() 