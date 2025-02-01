from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from firebase_config import db
import yfinance as yf
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

account_bp = Blueprint('account', __name__)

@account_bp.route('/api/v1/account/<user_id>', methods=['GET'])
@cross_origin()
def get_account(user_id):
    try:
        user_collection_ref = db.collection(f'portfolios_{user_id}')
        owned = None
        tickers = []
        first_name = ""
        last_name = ""
        state_of_residence = ""
        start_date = None
        doc_id = None
        
        for doc in user_collection_ref.stream():
            doc_data = doc.to_dict()
            tickers.extend(doc_data.get('tickers', []))
            owned = doc_data.get('owned', None)
            first_name = doc_data.get('first_name', "")
            last_name = doc_data.get('last_name', "")
            state_of_residence = doc_data.get('state_of_residence', "")
            start_date = doc_data.get('start_date', None)
            doc_id = doc.id

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            years_owned = (datetime.today() - start_date).days // 365
        else:
            years_owned = 0

        # Update the years_owned field in Firestore
        if doc_id:
            doc_ref = user_collection_ref.document(doc_id)
            doc_ref.update({'years_owned': years_owned})

        total_portfolio_value = 0
        ticker_values = {}

        for ticker in tickers:
            stock_ticker = ticker['ticker']
            shares = ticker['value']
            stock_data = yf.Ticker(stock_ticker)
            stock_price = stock_data.history(period='1d')['Close'].iloc[-1]
            ticker_value = shares * stock_price
            ticker_values[stock_ticker] = ticker_value
            total_portfolio_value += ticker_value

        ticker_percentages = [{'ticker': ticker, 'percentage': (value / total_portfolio_value) * 100} for ticker, value in ticker_values.items()]

        logging.debug(f"Retrieved tickers for user_id {user_id}: {tickers}")
        logging.debug(f"Total portfolio value for user_id {user_id}: {total_portfolio_value}")
        logging.debug(f"Ticker percentages for user_id {user_id}: {ticker_percentages}")

        return jsonify({
            'tickers': tickers,
            'total_portfolio_value': total_portfolio_value,
            'ticker_percentages': ticker_percentages,
            'first_name': first_name,
            'last_name': last_name,
            'state_of_residence': state_of_residence,
            'years_owned': years_owned,
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving account details: {e}")
        return jsonify({'error': str(e)}), 500

@account_bp.route('/api/v1/account/<user_id>/update-account', methods=['PUT'])
@cross_origin()
def update_account(user_id):
    try:
        data = request.json
        logging.debug(f"Received data for updating account: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_collection_ref = db.collection(f'portfolios_{user_id}')
        docs = user_collection_ref.stream()
        doc_id = None
        
        for doc in docs:
            doc_id = doc.id
            break
        
        if doc_id:
            doc_ref = user_collection_ref.document(doc_id)
            if 'years_owned' in data:
                del data['years_owned']  # Remove years_owned from the data if present
            doc_ref.update(data)
            logging.debug(f"Updated account for user_id {user_id} with data {data}")
            return jsonify({'message': 'Account updated successfully'}), 200
        else:
            return jsonify({'error': 'No document found for the user'}), 400
    except Exception as e:
        logging.error(f"Error updating account: {e}")
        return jsonify({'error': str(e)}), 500

@account_bp.route('/api/v1/account/<user_id>/set-status', methods=['PUT'])
def set_status(user_id):
    pass

@account_bp.route('/api/v1/account/<user_id>/delete-account', methods=['DELETE'])
@cross_origin()
def delete_account(user_id):
    try:
        user_collection_ref = db.collection(f'portfolios_{user_id}')
        docs = user_collection_ref.stream()
        doc_id = None
        
        for doc in docs:
            doc_id = doc.id
            break
        
        if doc_id:
            doc_ref = user_collection_ref.document(doc_id)
            doc_ref.delete()
            logging.debug(f"Deleted account for user_id {user_id}")
            return jsonify({'message': 'Account deleted successfully'}), 200
        else:
            return jsonify({'error': 'No document found for the user'}), 400
    except Exception as e:
        logging.error(f"Error deleting account: {e}")
        return jsonify({'error': str(e)}), 500