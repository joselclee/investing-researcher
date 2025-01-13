import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from scipy.optimize import minimize

end_date = datetime.today()

tickers = ['SPY', 'BND', 'GLD', 'QQQ', 'VTI']
years = 30
start_date = end_date - timedelta(days=years*365)
adj_close_df = pd.DataFrame()
for ticker in tickers:
    try:
        print(f"Downloading data for {ticker}...")
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        print(f"Data for {ticker}:\n{data.head()}\n")  # Print the first few rows of the data
        if 'Close' in data.columns:
            adj_close_df[ticker] = data['Close']
        else:
            print(f"No 'Close' data for {ticker}")
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        
log_returns = np.log(adj_close_df / adj_close_df.shift(1)).dropna()

cov_matrix = log_returns.cov()*252 # Annualize the covariance matrix

def standard_deviation (weights, cov_matrix):
    variance = weights.T @ cov_matrix @ weights #Transposes the weights vector, multiplies it by the covariance matrix, and then multiplies the result by the weights vector
    return np.sqrt(variance)

def expected_return(weights, log_returns):
    return np.sum(log_returns.mean() * weights)*252

#Sharpe Ratio
def sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate):
    return(expected_return(weights, log_returns) - risk_free_rate) / standard_deviation(weights, cov_matrix)

#Set the risk free rate
from fredapi import Fred
fred = Fred(api_key='8b0d64958f6457138a9c7e722e5c12d5')
ten_year_treasury_rate = fred.get_series_latest_release('GS10') / 100

risk_free_rate = ten_year_treasury_rate.iloc[-1]
# print(risk_free_rate)

def neg_sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate):
    return -sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate)
constraints = {'type': 'eq',
               'fun': lambda x: np.sum(x) - 1}
bounds =[(0, 0.5) for _ in range(len(tickers))]

# Set initial weights
initial_weights = np.array([1/len(tickers)] * len(tickers))

#Optimize the weights to maximize Sharpe Ratio
optimized_results = minimize(neg_sharpe_ratio, 
                             initial_weights, 
                             args=(log_returns, cov_matrix, risk_free_rate), 
                             method='SLSQP', 
                             constraints = constraints, 
                             bounds = bounds)

optimal_weights = optimized_results.x
print(f"Optimal Weights: {optimal_weights}")
for ticker, weight in zip(tickers, optimal_weights):
    print(f"{ticker}: {weight:.4f}")

optimal_portfolio_return = expected_return(optimal_weights, log_returns)
optimal_portfolio_volatility = standard_deviation(optimal_weights, cov_matrix)
optimal_portfolio_sharpe_ratio = sharpe_ratio(optimal_weights, log_returns, cov_matrix, risk_free_rate)

print(f"Optimal Portfolio Return: {optimal_portfolio_return:.4f}")
print(f"Optimal Portfolio Volatility: {optimal_portfolio_volatility:.4f}")
print(f"Optimal Portfolio Sharpe Ratio: {optimal_portfolio_sharpe_ratio:.4f}")

