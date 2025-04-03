#!/bin/bash
# This script cleans up the repository for GitHub

echo "Cleaning up repository for GitHub..."

# Remove test files
echo "Removing test files..."
find . -name "test_*.py" -type f -delete

# Remove __pycache__ directories
echo "Removing Python cache directories..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -type f -delete
find . -name "*.pyo" -type f -delete
find . -name "*.pyd" -type f -delete

# Remove egg-info directory
echo "Removing packaging metadata..."
rm -rf btc_prediction_market.egg-info
rm -f setup.py

# Remove empty price_feed directory but keep the package structure
echo "Cleaning empty directories..."
if [ -d "btc_prediction_market/price_feed" ]; then
    mkdir -p btc_prediction_market/price_feed
    touch btc_prediction_market/price_feed/__init__.py
fi

# Remove basic_binary_market directory if it exists and is not part of the project
echo "Removing unnecessary directories..."
if [ -d "basic_binary_market" ]; then
    rm -rf basic_binary_market
fi

# Remove SOLUTION_SUMMARY.md if it exists
if [ -f "SOLUTION_SUMMARY.md" ]; then
    rm -f SOLUTION_SUMMARY.md
fi

# Remove README_clean.md if it exists (we're using the updated original README)
if [ -f "README_clean.md" ]; then
    rm -f README_clean.md
fi

# Create empty directories if they don't exist to maintain package structure
mkdir -p btc_prediction_market/market_model
mkdir -p btc_prediction_market/simulators

echo "Cleanup completed successfully!"
echo "You can now push your cleaned repository to GitHub." 