from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf
from scipy.stats import norm

monte_carlo_var_bp = Blueprint('monte_carlo_var', __name__)

@monte_carlo_var_bp.route('/api/v1/monte-carlo-var', methods=['POST'])
@cross_origin()
def monte_carlo_var():
    data = request.json
    tickers = data.get('tickers', ['SPY', 'BND', 'GLD', 'QQQ', 'VTI'])

    years = int(data.get('years', 15))  # Ensure years is an integer
    portfolio_value = float(data.get('portfolio_value', 10000))  # Ensure portfolio_value is a float
    days = int(data.get('days', 5))  # Ensure days is an integer
    simulations = int(data.get('simulations', 100000))  # Ensure simulations is an integer
    confidence_interval = float(data.get('confidence_interval', 0.95))  # Ensure confidence_interval is a float
    weights = data.get('weights')

    endDate = dt.datetime.now()
    startDate = endDate - dt.timedelta(days=years*365)
    adj_close_df = pd.DataFrame()

    for ticker in tickers:
        try:
            data = yf.download(ticker, start=startDate, end=endDate, progress=False)
            if 'Close' in data.columns:
                adj_close_df[ticker] = data['Close']
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    log_returns = np.log(adj_close_df / adj_close_df.shift(1)).dropna()
    cov_matrix = log_returns.cov()

    def expected_return(weights, log_returns):
        return np.sum(log_returns.mean() * weights)

    def standard_deviation(weights, cov_matrix):
        variance = weights.T @ cov_matrix @ weights
        return np.sqrt(variance)

    if weights:
        if len(weights) != len(tickers):
            return jsonify({'error': 'Number of weights must match number of tickers'}), 400
        weights = np.array(weights, dtype=float)  # Ensure weights are floats
    else:
        weights = np.array([1/len(tickers)] * len(tickers), dtype=float)  # Ensure weights are floats

    portfolio_expected_return = expected_return(weights, log_returns)
    portfolio_std_dev = standard_deviation(weights, cov_matrix)

    def random_z_score():
        return np.random.normal(0, 1)

    def scenario_gain_loss(portfolio_value, portfolio_std_dev, z_score, days):
        return portfolio_value * portfolio_expected_return * days + portfolio_value * portfolio_std_dev * z_score * np.sqrt(days)

    scenario_return = []
    for i in range(simulations):
        z_score = random_z_score()
        scenario_return.append(scenario_gain_loss(portfolio_value, portfolio_std_dev, z_score, days))

    VaR = -np.percentile(scenario_return, 100 * (1 - confidence_interval))

    return jsonify({
        'VaR': VaR,
        'scenario_return': scenario_return
    })