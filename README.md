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

- **How It Works**: Orders are matched in order of price priority, and then time priority for orders at the same price.
- **Execution Rules**:
  - BUY orders match with SELL orders at the same price or lower
  - SELL orders match with BUY orders at the same price or higher
  - Older orders at the same price level are executed before newer ones
- **Comparison with Other Algorithms**:
  - **Price-Time (implemented)**: Fair, transparent, and rewards early order placement
  - **Pro-Rata**: Would distribute fills proportionally across orders at the same price, regardless of timestamp
  - **Top-of-Book**: Would only match against the best price level, potentially leaving partial executions

### Market Resolution

The market resolves in a binary fashion:

- **YES Resolution**: If BTC reaches the target price, all YES tokens pay out 1 unit, and NO tokens pay 0
- **NO Resolution**: If BTC fails to reach the target price within the timeframe, all NO tokens pay out 1 unit, and YES tokens pay 0
- **Resolution Mechanism**: The system monitors BTC price continuously and automatically resolves the market when conditions are met

### Probability of resolution

**Logistic Regression Model**: This project utilizes a logistic regression model to estimate the probability of resolution based on current market conditions and historical data. The logistic regression model is particularly suited for binary outcomes, making it ideal for predicting the likelihood of an event occurring (e.g., whether BTC will reach a specified price).

  - **Model Structure**: The logistic regression model is defined by the logistic function:
    \[
    P(x) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x_1 + \beta_2 x_2 + ... + \beta_n x_n)}}
    \]
    where:
    - \(P(x)\) is the predicted probability of resolution.
    - \(x_1, x_2, ..., x_n\) are the input features (e.g., current price, time remaining, trading volume, market sentiment).
    - \(\beta_0\) is the intercept, and \(\beta_1, \beta_2, ..., \beta_n\) are the coefficients for each feature, which are learned from historical data.

  - **Input Features**: The model uses various features to predict the probability of resolution, including:
    - **Current Price**: The current market price of BTC.
    - **Time Remaining**: The time left until the market closes or the event is resolved.
    - **Trading Volume**: The volume of trades occurring in the market, which can indicate market interest and liquidity.
    - **Market Sentiment**: Sentiment analysis derived from news articles, social media, or other sources that may influence market behavior.

  - **Training the Model**: The model is trained using historical data from previous prediction markets. The training process involves:
    - Collecting historical data on BTC prices and market conditions.
    - Labeling the data based on whether the event resolved positively (YES) or negatively (NO).
    - Using a training algorithm (e.g., gradient descent) to optimize the coefficients (\(\beta\)) that minimize the difference between predicted probabilities and actual outcomes.

  - **Probability Estimation**: Once trained, the model can be used to estimate the probability of resolution in real-time as market conditions change. The logistic function ensures that the predicted probabilities are bounded between 0 and 1, making them interpretable as probabilities.

  - **Advantages**: The logistic regression model provides a smooth transition of probabilities, allowing for a realistic representation of the likelihood of a particular outcome. It is also relatively simple to implement and interpret, making it a suitable choice for this prediction market application.


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