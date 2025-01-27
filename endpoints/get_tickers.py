# endpoints/get_tickers.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from firebase_config import db
import logging
import yfinance as yf

logging.basicConfig(level=logging.DEBUG)

get_tickers_bp = Blueprint('get_tickers', __name__)

@get_tickers_bp.route('/api/v1/get-tickers', methods=['GET'])
@cross_origin()
def get_tickers():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        # Access the user's collection
        user_collection_ref = db.collection(f'portfolios_{user_id}')
        tickers = []
        for doc in user_collection_ref.stream():
            tickers.extend(doc.to_dict().get('tickers', []))

        # Fetch the latest stock prices
        total_portfolio_value = 0
        for ticker in tickers:
            stock_ticker = ticker['ticker']
            shares = ticker['value']
            stock_data = yf.Ticker(stock_ticker)
            stock_price = stock_data.history(period='1d')['Close'].iloc[-1]
            total_portfolio_value += shares * stock_price

        logging.debug(f"Retrieved tickers for user_id {user_id}: {tickers}")
        logging.debug(f"Total portfolio value for user_id {user_id}: {total_portfolio_value}")
        return jsonify({'tickers': tickers, 'total_portfolio_value': total_portfolio_value}), 200
    except Exception as e:
        logging.error(f"Error retrieving tickers: {e}")
        return jsonify({'error': str(e)}), 500