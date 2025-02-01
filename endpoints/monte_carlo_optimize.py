from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
import logging
from arch import arch_model  # For GARCH modeling
from fredapi import Fred  # For macroeconomic data
from multiprocessing import Pool  # For parallel processing
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

monte_carlo_optimization_bp = Blueprint('monte_carlo_optimization', __name__)

# Initialize FRED API
fred_api_key = os.getenv('FRED_API_KEY')
fred = Fred(api_key=fred_api_key)

@monte_carlo_optimization_bp.route('/api/v1/optimize/monte-carlo', methods=['POST'])
@cross_origin()
def monte_carlo_optimization():
    data = request.json
    logging.debug(f"Received data: {data}")

    ticker_weights = data.get('ticker_weights', [])
    start_date = data.get('start_date', '2020-01-01')
    end_date = data.get('end_date', '2023-01-01')
    num_scenarios = int(data.get('num_scenarios', 1000))
    risk_free_rate = float(data.get('risk_free_rate', 0.02))

    if not ticker_weights:
        return jsonify({'error': 'Ticker weights are required'}), 400

    def fetch_historical_data(tickers, start_date, end_date):
        valid_tickers = []
        for ticker in tickers:
            try:
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if not data.empty:
                    valid_tickers.append(ticker)
            except Exception as e:
                logging.error(f"Error fetching data for {ticker}: {e}")
        
        if not valid_tickers:
            raise ValueError("No valid tickers found.")
        
        data = yf.download(valid_tickers, start=start_date, end=end_date)['Close']
        return data

    def calculate_returns(data):
        returns = data.pct_change().dropna()
        return returns

    def fetch_macroeconomic_data():
        # Fetch risk-free rate (10-year Treasury yield) from FRED
        risk_free_rate = fred.get_series('DGS10').iloc[-1] / 100
        logging.debug(f"Fetched risk-free rate: {risk_free_rate}")
        return risk_free_rate

    def fit_garch_model(returns):
        # Fit a GARCH(1,1) model to the returns
        model = arch_model(returns, vol='Garch', p=1, q=1)
        fitted_model = model.fit(disp='off')
        return fitted_model

    def generate_stochastic_scenarios(returns, num_scenarios=1000):
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Ensure covariance matrix is positive semi-definite
        if not np.all(np.linalg.eigvals(cov_matrix) >= 0):
            cov_matrix = nearest_positive_semi_definite(cov_matrix)

        simulated_returns = np.random.multivariate_normal(mean_returns, cov_matrix, num_scenarios)
        return simulated_returns

    def nearest_positive_semi_definite(matrix):
        from scipy.linalg import sqrtm
        sym_matrix = (matrix + matrix.T) / 2
        eigvals, eigvecs = np.linalg.eig(sym_matrix)
        eigvals[eigvals < 0] = 0
        return eigvecs @ np.diag(eigvals) @ eigvecs.T

    def objective_function(weights, simulated_returns, risk_free_rate):
        portfolio_returns = np.dot(simulated_returns, weights)
        portfolio_mean_return = np.mean(portfolio_returns)
        portfolio_std = np.std(portfolio_returns)
        sharpe_ratio = (portfolio_mean_return - risk_free_rate) / portfolio_std
        return -sharpe_ratio
    
    def validate_and_normalize_weights(ticker_weights):
        valid_tickers = []
        valid_weights = []
        total_weight = 0

        for item in ticker_weights:
            ticker = item['ticker']
            weight = item['weight']
            if isinstance(weight, (int, float)) and weight > 0:
                valid_tickers.append(ticker)
                valid_weights.append(weight)
                total_weight += weight

        if not valid_tickers:
            raise ValueError("No valid tickers or weights found.")

        # Normalize weights
        normalized_weights = [weight / total_weight for weight in valid_weights]

        return valid_tickers, normalized_weights

    def optimize_portfolio(ticker_weights, start_date, end_date, num_scenarios=1000, risk_free_rate=0.02):
        # Validate and normalize weights
        tickers, initial_weights = validate_and_normalize_weights(ticker_weights)

        # Fetch historical data
        historical_data = fetch_historical_data(tickers, start_date, end_date)
        if historical_data.empty:
            raise ValueError("No historical data found for the given tickers.")

        # Calculate returns
        returns = calculate_returns(historical_data)
        if returns.empty:
            raise ValueError("No returns calculated for the given tickers.")

        # Generate stochastic scenarios
        simulated_returns = generate_stochastic_scenarios(returns, num_scenarios)

        # Optimize portfolio
        constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
        bounds = tuple((0, 1) for _ in range(len(tickers)))
        result = minimize(
            objective_function,
            initial_weights,
            args=(simulated_returns, risk_free_rate),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        # Extract optimized weights
        optimized_weights = result.x

        # Calculate portfolio performance metrics
        portfolio_returns = np.dot(simulated_returns, optimized_weights)
        portfolio_mean_return = np.mean(portfolio_returns)
        portfolio_std = np.std(portfolio_returns)
        sharpe_ratio = (portfolio_mean_return - risk_free_rate) / portfolio_std

        return {
            'optimized_weights': dict(zip(tickers, optimized_weights)),
            'mean_return': portfolio_mean_return,
            'std_dev': portfolio_std,
            'sharpe_ratio': sharpe_ratio
        }

    try:
        # Fetch macroeconomic data (e.g., risk-free rate)
        risk_free_rate = fetch_macroeconomic_data()

        # Optimize portfolio
        result = optimize_portfolio(ticker_weights, start_date, end_date, num_scenarios, risk_free_rate)
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error in optimization: {e}")
        return jsonify({'error': str(e)}), 500