from setuptools import setup, find_packages

setup(
    name="basic_binary_market",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
    ],
    description="A lightweight prediction market simulator for BTC price",
    author="BTC Prediction Market Team",
    python_requires=">=3.7",
) 