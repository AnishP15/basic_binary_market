# BTC Prediction Market

A binary prediction market simulator for Bitcoin price movements. This project lets you place orders in a prediction market for questions like "Will BTC reach $100,000 in 24 hours?".

## Features

- Interactive command-line interface for placing orders
- Real-time order book visualization with bid-ask spreads
- Limit and market order types
- Order matching engine with price-time priority
- Simple BTC price simulator
- Balanced initial liquidity with clean price levels

## Technical Architecture

### Order Book Structure

The order book is implemented as a binary market with two complementary assets (YES and NO):

- **Data Structure**: The core order book is organized as a dictionary of lists, separated by option type (YES/NO) and side (BUY/SELL).
- **Order Sorting**: 
  - BUY orders are sorted in descending order by price (highest first)
  - SELL orders are sorted in ascending order by price (lowest first)
- **Order Representation**: Each order contains a unique ID, price, size, user ID, and timestamp.
- **Price Level Aggregation**: The order book summary aggregates orders at the same price level while maintaining individual order details for matching.

### Matching Algorithm

This project implements **price-time priority** (also known as FIFO - First In, First Out) matching:

- **How It Works**: Orders are matched in order of price priority, and then time priority for orders at the same price.
- **Execution Rules**:
  - BUY orders match with SELL orders at the same price or lower
  - SELL orders match with BUY orders at the same price or higher
  - Older orders at the same price level are executed before newer ones
- **Comparison with Other Algorithms**:
  - **Price-Time (implemented)**: Fair, transparent, and rewards early order placement
  - **Pro-Rata**: Would distribute fills proportionally across orders at the same price, regardless of timestamp
  - **Top-of-Book**: Would only match against the best price level, potentially leaving partial executions
  - **Direct/CLOB (implemented)**: Maintains a central limit order book with transparent matching rules

### Market Resolution

The market resolves in a binary fashion:

- **YES Resolution**: If BTC reaches the target price, all YES tokens pay out 1 unit, and NO tokens pay 0
- **NO Resolution**: If BTC fails to reach the target price within the timeframe, all NO tokens pay out 1 unit, and YES tokens pay 0
- **Resolution Mechanism**: The system monitors BTC price continuously and automatically resolves the market when conditions are met

### Alternative Approaches

Several alternative approaches could have been implemented:

- **Automated Market Maker (AMM)**: Instead of a CLOB, an AMM with a bonding curve (like Uniswap's x*y=k) could have been used, requiring less liquidity but potentially worse pricing
- **Dynamic Parimutuel**: Could have implemented dynamic odds that adjust based on total money wagered on each side
## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/kalshi_market_making.git
cd kalshi_market_making
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:

```bash
python -m btc_prediction_market.main
```

You can customize the target price and timeframe:

```bash
python -m btc_prediction_market.main --target 100000 --timeframe 24
```

### Available Commands

- `help` - Show help information
- `limit <side> <option> <price> <size>` - Place a limit order (e.g., `limit buy yes 0.7 10`)
- `market <side> <option> <size>` - Place a market order (e.g., `market sell no 5`)
- `cancel <id>` - Cancel an order by ID
- `exit` or `quit` - Exit the simulator

### Order Book Display

The order book display shows:
- All buy and sell orders for both YES and NO markets
- The bid-ask spread for each market with percentage
- Order counts at each price level
- Clean price formatting for better readability

## Project Structure

- `btc_prediction_market/main.py` - Main application module and CLI interface
- `btc_prediction_market/market_model/` - Order matching engine and market model
  - `binary_market.py` - Core market implementation with order matching algorithm
  - `order.py` - Order data model and related operations
- `btc_prediction_market/simulators/` - BTC price simulation
  - `btc_simulator.py` - Simulates BTC price movements using stochastic processes
  - `price_feed.py` - Provides real or simulated price data

## License

MIT


