# BTC Prediction Market

A binary prediction market simulator for Bitcoin price movements. This project lets you place orders in a prediction market for questions like "Will BTC reach $100,000 in 24 hours?".

## Features

- Interactive command-line interface for placing orders
- Real-time order book visualization with bid-ask spreads
- Limit and market order types
- Order matching engine with price-time priority
- Simple BTC price feed
- Balanced initial liquidity 

## Technical Architecture

### Order Book Architecture

The order book is implemented as a binary market with two complementary assets (YES and NO). Here's a detailed breakdown of its architecture:

- **Data Structure**: The core order book is organized as a dictionary of lists, separated by option type (YES/NO) and side (BUY/SELL). Each entry in the dictionary contains a list of orders for that specific option type and side.

- **Adding Orders**:
  - When a new order is added, it is placed in the appropriate list based on its type (BUY/SELL) and side (YES/NO).
  - **Time Complexity**: The time complexity for adding an order is O(n) in the worst case, where n is the number of orders at the same price level.

- **Order Matching**:
  - The matching algorithm follows a price-time priority (FIFO - First In, First Out) approach. Orders are matched based on price priority first, and then by time for orders at the same price.
  - **Execution Rules**:
    - BUY orders match with SELL orders at the same price or lower.
    - SELL orders match with BUY orders at the same price or higher.
    - Older orders at the same price level are executed before newer ones.
  - **Time Complexity**: The time complexity for matching orders is O(m) in the worst case, where m is the number of orders in the order book that need to be checked for matching.

- **Price Level Aggregation**: The order book summary aggregates orders at the same price level while maintaining individual order details for matching. This allows for efficient execution and clear visibility of the market depth.

### Matching Algorithm

This project implements **price-time priority** (also known as FIFO - First In, First Out) matching:

- **How It Works**: Orders are matched in order of price priority, and then time priority for orders at the same price. This approach is fair, transparent, and rewards early order placement
- **Execution Rules**:
  - BUY orders match with SELL orders at the same price or lower
  - SELL orders match with BUY orders at the same price or higher
  - Older orders at the same price level are executed before newer ones
- **Comparison with Other Algorithms**:
  - **Pro-Rata**: Would distribute fills proportionally across orders at the same price, regardless of timestamp
  - **Top-of-Book**: Would only match against the best price level, potentially leaving partial executions
  - **Lead Market Maker**: This algorithm involves a designated participant (the lead market maker) who provides liquidity to the market by placing orders at various price levels. The lead market maker can help stabilize prices and ensure that there is always a market for participants to trade in. This approach can enhance market efficiency and reduce volatility by ensuring that there are always buy and sell orders available.

### Market Resolution

The market resolves in a binary fashion:

- **YES Resolution**: If BTC reaches the target price, all YES tokens pay out 1 unit, and NO tokens pay 0
- **NO Resolution**: If BTC fails to reach the target price within the timeframe, all NO tokens pay out 1 unit, and YES tokens pay 0

### Probability of resolution

**Logistic Regression Model**: This project utilizes a logistic regression model to estimate the probability of resolution based on current market conditions and historical data. The function calculates how far the current price is from the target price as a percentage (distance_pct).

It factors in the remaining time (time_factor) until the deadline, and the current volatility, scaled by the square root of remaining hours.

These values are combined into a single parameter z, which is passed into the logistic function:

```python
z = -distance_pct / (vol_factor * sensitivity) + time_factor
probability = expit(z)
```

The logistic function then outputs a probability between 0 and 1, where:
   - Higher volatility → higher chance to reach the target (more potential price movement)
   - More time left → more opportunity to reach the goal
   - Smaller distance to target → higher likelihood of success

### Alternative Approaches

Several alternative approaches could have been implemented to model the probability of resolution:

- **Random Walk Model**: This model assumes that price movements are random and independent of past changes. It can be used to estimate the likelihood of reaching a certain price level over time, providing insights into the probability of an event occurring based on historical price movements.

- **Black-Scholes Model**: Originally designed for pricing options, the Black-Scholes model can be adapted to estimate the probability of resolution in prediction markets. It considers factors such as current price, strike price, volatility, and time to expiration to calculate the likelihood of an outcome.

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/kalshi_market_making.git
cd kalshi_market_making
```
2. Install the required dependencies:
```
pip install -r requirements.txt
```
3. Run the application: 
```
python -m basic_binary_market.main
```
4. (Optional) Customize parameters:
```
python -m btc_prediction_market.main --target 100000 --timeframe 24
```