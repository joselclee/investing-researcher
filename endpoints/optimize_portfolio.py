from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf
from scipy.optimize import minimize
from fredapi import Fred
import os
from dotenv import load_dotenv
import logging

load_dotenv()

optimize_portfolio_bp = Blueprint('optimize_portfolio', __name__)

@optimize_portfolio_bp.route('/api/v1/optimize-portfolio', methods=['POST'])
@cross_origin()
def optimize_portfolio():
    data = request.json
    logging.debug(f"Received data: {data}")

    tickers = data.get('tickers', [])
    weights = data.get('weights', [])

    logging.debug(f"Tickers data: {tickers}")
    logging.debug(f"Weights data: {weights}")

    # Ensure tickers is a list of strings and weights is a list of floats
    if not isinstance(tickers, list) or not all(isinstance(ticker, str) for ticker in tickers):
        logging.error(f"Tickers data is not a list of strings: {tickers}")
        return jsonify({'error': 'Tickers data must be a list of strings'}), 400

    if not isinstance(weights, list) or not all(isinstance(weight, (int, float, str)) for weight in weights):
        logging.error(f"Weights data is not a list of numbers: {weights}")
        return jsonify({'error': 'Weights data must be a list of numbers'}), 400

    # Convert weights to floats
    try:
        weights = [float(weight) for weight in weights]
    except ValueError as e:
        logging.error(f"Error converting weights to floats: {e}")
        return jsonify({'error': 'Weights must be convertible to floats'}), 400

    # Ensure the number of tickers matches the number of weights
    if len(tickers) != len(weights):
        logging.error(f"Number of tickers does not match number of weights: {len(tickers)} vs {len(weights)}")
        return jsonify({'error': 'Number of tickers must match number of weights'}), 400

    # Aggregate values of duplicate tickers
    tickers_dict = {}
    for ticker, weight in zip(tickers, weights):
        if ticker in tickers_dict:
            tickers_dict[ticker] += weight
        else:
            tickers_dict[ticker] = weight

    tickers = list(tickers_dict.keys())
    weights = list(tickers_dict.values())

    logging.debug(f"Aggregated tickers: {tickers}")
    logging.debug(f"Aggregated weights: {weights}")

    years = int(data.get('years', 30))  # Ensure years is an integer
    end_date = dt.datetime.today()
    start_date = end_date - dt.timedelta(days=years*365)
    adj_close_df = pd.DataFrame()

    for ticker in tickers:
        try:
            logging.debug(f"Processing ticker: {ticker}")
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if 'Close' in data.columns:
                adj_close_df[ticker] = data['Close']
        except Exception as e:
            logging.error(f"Error downloading data for ticker {ticker}: {e}")
            return jsonify({'error': str(e)}), 500

    log_returns = np.log(adj_close_df / adj_close_df.shift(1)).dropna()
    cov_matrix = log_returns.cov() * 252

    def standard_deviation(weights, cov_matrix):
        variance = weights.T @ cov_matrix @ weights
        return np.sqrt(variance)

    def expected_return(weights, log_returns):
        logging.debug(f"log_returns.mean(): {log_returns.mean()}")
        logging.debug(f"weights: {weights}")
        return np.sum(log_returns.mean() * weights) * 252

    def sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate):
        return (expected_return(weights, log_returns) - risk_free_rate) / standard_deviation(weights, cov_matrix)

    fred_api_key = os.getenv('FRED_API_KEY')
    fred = Fred(api_key=fred_api_key)
    ten_year_treasury_rate = fred.get_series_latest_release('GS10') / 100
    risk_free_rate = ten_year_treasury_rate.iloc[-1]

    def neg_sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate):
        return -sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate)

    def weight_sum_constraint(weights):
        return np.sum(weights) - 1

    constraints = [
        {'type': 'eq', 'fun': weight_sum_constraint},  # Sum of weights must be 1
    ]
    bounds = [(0, 1) for _ in range(len(tickers))]  # Each weight can be between 0 and 1
    initial_weights = np.array([1/len(tickers)] * len(tickers), dtype=float)  # Ensure initial_weights are floats

    logging.debug(f"Initial weights: {initial_weights}")
    logging.debug(f"Log returns shape: {log_returns.shape}")
    logging.debug(f"Covariance matrix shape: {cov_matrix.shape}")

    optimized_results = minimize(neg_sharpe_ratio, initial_weights, args=(log_returns, cov_matrix, risk_free_rate), method='SLSQP', constraints=constraints, bounds=bounds)
    optimal_weights = optimized_results.x

    # Round the weights to the nearest two decimals
    optimal_weights = np.round(optimal_weights, 2)

    # Ensure the sum of weights is 1
    if np.sum(optimal_weights) > 1:
        optimal_weights = optimal_weights / np.sum(optimal_weights)

    return jsonify({
        'optimal_weights': optimal_weights.tolist(),
        'optimal_portfolio_return': expected_return(optimal_weights, log_returns),
        'optimal_portfolio_volatility': standard_deviation(optimal_weights, cov_matrix),
        'optimal_portfolio_sharpe_ratio': sharpe_ratio(optimal_weights, log_returns, cov_matrix, risk_free_rate)
    })