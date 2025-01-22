import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf
import matplotlib.pyplot as plt
from scipy.stats import norm

# Define the number of years for historical data
years = 10

# Define the start and end dates for data download
endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=years*365)

# List of tickers to download data for
tickers = ['SPY']

# Initialize an empty DataFrame to store adjusted close prices
adj_close_df = pd.DataFrame()

# Download the daily adjusted close prices for the tickers
for ticker in tickers:
    try:
        print(f"Downloading data for {ticker}...")
        data = yf.download(ticker, start=startDate, end=endDate, progress=False)
        print(f"Data for {ticker}:\n{data.head()}\n")  # Print the first few rows of the data
        if 'Close' in data.columns:
            adj_close_df[ticker] = data['Close']
        else:
            print(f"No 'Close' data for {ticker}")
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")

# Calculate daily log returns and drop NAs
log_returns = np.log(adj_close_df / adj_close_df.shift(1)).dropna()
print(log_returns)

def expected_return(weights, log_returns):
    return np.sum(log_returns.mean() * weights)

def standard_deviation(weights, cov_matrix):
    variance = weights.T @ cov_matrix @ weights
    return np.sqrt(variance)

cov_matrix = log_returns.cov()
portfolio_value = 10000  # Hardcoded $1,000,000 portfolio value
weights = np.array([1/len(tickers)] * len(tickers))
portfolio_expected_return = expected_return(weights, log_returns)
portfolio_std_dev = standard_deviation(weights, cov_matrix)

def random_z_score():
    return np.random.normal(0, 1)

days = 5

def scenario_gain_loss(portfolio_value, portfolio_std_dev, z_score, days):
    return portfolio_value * portfolio_expected_return * days + portfolio_value * portfolio_std_dev * z_score * np.sqrt(days)

simulations = 1000  # Number of simulations
scenario_return = []
for i in range(simulations):
    z_score = random_z_score()
    scenario_return.append(scenario_gain_loss(portfolio_value, portfolio_std_dev, z_score, days))

confidence_interval = 0.95
VaR = -np.percentile(scenario_return, 100 * (1 - confidence_interval))
print(f"Value at Risk (95% confidence): ${VaR:,.2f}")


# # Plot the histogram of scenario returns
# plt.hist(scenario_return, bins=50, density=True, alpha=0.6, color='g')

# # Plot the VaR line
# plt.axvline(x=VaR, color='r', linestyle='--', label=f'VaR (95%): ${VaR:,.2f}')

# # Plot the mean line
# mean_return = np.mean(scenario_return)
# plt.axvline(x=mean_return, color='b', linestyle='-', label=f'Mean: ${mean_return:,.2f}')

# # Add labels and title
# plt.xlabel('Scenario Gain/Loss ($)')
# plt.ylabel('Density')
# plt.title('Monte Carlo Simulation for Value at Risk')
# plt.legend()

# # Show the plot
# plt.show()
