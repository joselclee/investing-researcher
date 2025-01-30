# endpoints/day_history.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from firebase_config import db
import yfinance as yf
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)

day_history_bp = Blueprint('day_history', __name__)

@day_history_bp.route('/api/v1/day-history/<user_id>', methods=['GET'])
@cross_origin()
def day_history(user_id):
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        # Access the user's collection
        user_collection_ref = db.collection(f'portfolios_{user_id}')
        tickers = []
        for doc in user_collection_ref.stream():
            tickers.extend(doc.to_dict().get('tickers', []))

        if not tickers:
            return jsonify({'error': 'No tickers found for the user'}), 404

        # Fetch the day history for each ticker
        portfolio_history = pd.DataFrame()
        weights = {}
        for ticker in tickers:
            stock_ticker = ticker['ticker']
            shares = ticker['value']
            stock_data = yf.Ticker(stock_ticker)
            history = stock_data.history(period='1d', interval='15m')  # Fetch 15-minute interval data for the last day
            portfolio_history[stock_ticker] = history['Close']
            weights[stock_ticker] = shares

        # Calculate the total portfolio value at each time point
        for ticker, shares in weights.items():
            portfolio_history[ticker] *= shares

        portfolio_performance = portfolio_history.sum(axis=1)

        # Convert the index (timestamps) to strings for JSON serialization
        portfolio_performance.index = portfolio_performance.index.astype(str)

        logging.debug(f"Retrieved day history for user_id {user_id}")
        return jsonify({'portfolio_performance': portfolio_performance.to_dict()}), 200
    except Exception as e:
        logging.error(f"Error retrieving day history: {e}")
        return jsonify({'error': str(e)}), 500