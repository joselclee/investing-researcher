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
load_dotenv()

optimize_portfolio_bp = Blueprint('optimize_portfolio', __name__)

@optimize_portfolio_bp.route('/api/v1/optimize-portfolio', methods=['POST'])
@cross_origin()
def optimize_portfolio():
    data = request.json
    tickers = data.get('tickers', ['SPY', 'BND', 'GLD', 'QQQ', 'VTI'])

    years = int(data.get('years', 30))  # Ensure years is an integer
    end_date = dt.datetime.today()
    start_date = end_date - dt.timedelta(days=years*365)
    adj_close_df = pd.DataFrame()

    for ticker in tickers:
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if 'Close' in data.columns:
                adj_close_df[ticker] = data['Close']
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    log_returns = np.log(adj_close_df / adj_close_df.shift(1)).dropna()
    cov_matrix = log_returns.cov() * 252

    def standard_deviation(weights, cov_matrix):
        variance = weights.T @ cov_matrix @ weights
        return np.sqrt(variance)

    def expected_return(weights, log_returns):
        return np.sum(log_returns.mean() * weights) * 252

    def sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate):
        return (expected_return(weights, log_returns) - risk_free_rate) / standard_deviation(weights, cov_matrix)

    fred_api_key = os.getenv('FRED_API_KEY')
    fred = Fred(api_key=fred_api_key)
    ten_year_treasury_rate = fred.get_series_latest_release('GS10') / 100
    risk_free_rate = ten_year_treasury_rate.iloc[-1]

    def neg_sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate):
        return -sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate)

    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Sum of weights must be 1
    ]
    bounds = [(0, 1) for _ in range(len(tickers))]  # Each weight can be between 0 and 1
    initial_weights = np.array([1/len(tickers)] * len(tickers), dtype=float)  # Ensure initial_weights are floats

    optimized_results = minimize(neg_sharpe_ratio, initial_weights, args=(log_returns, cov_matrix, risk_free_rate), method='SLSQP', constraints=constraints, bounds=bounds)
    optimal_weights = optimized_results.x

    return jsonify({
        'optimal_weights': optimal_weights.tolist(),
        'optimal_portfolio_return': expected_return(optimal_weights, log_returns),
        'optimal_portfolio_volatility': standard_deviation(optimal_weights, cov_matrix),
        'optimal_portfolio_sharpe_ratio': sharpe_ratio(optimal_weights, log_returns, cov_matrix, risk_free_rate)
    })