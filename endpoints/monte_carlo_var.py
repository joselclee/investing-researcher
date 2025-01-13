from flask import Blueprint, request, jsonify
import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf
from scipy.stats import norm

monte_carlo_var_bp = Blueprint('monte_carlo_var', __name__)

@monte_carlo_var_bp.route('/monte-carlo-var', methods=['POST'])
def monte_carlo_var():
    data = request.json
    tickers = data.get('tickers', ['SPY', 'BND', 'GLD', 'QQQ', 'VTI'])

    years = data.get('years', 15)
    portfolio_value = data.get('portfolio_value', 1000000)
    days = data.get('days', 5)
    simulations = data.get('simulations', 100000)
    confidence_interval = data.get('confidence_interval', 0.95)
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
        weights = np.array(weights)
    else:
        weights = np.array([1/len(tickers)] * len(tickers))

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