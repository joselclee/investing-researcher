# endpoints/remove_ticker.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from firebase_config import db
import logging

logging.basicConfig(level=logging.DEBUG)

remove_ticker_bp = Blueprint('remove_ticker', __name__)

@remove_ticker_bp.route('/api/v1/remove-ticker', methods=['POST'])
@cross_origin()
def remove_ticker():
    data = request.json
    logging.debug(f"Received data: {data}")
    user_id = data.get('user_id')
    ticker_to_remove = data.get('ticker')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    if not ticker_to_remove:
        return jsonify({'error': 'Ticker is required'}), 400

    try:
        # Access the user's collection
        user_collection_ref = db.collection(f'portfolios_{user_id}')
        tickers = []
        for doc in user_collection_ref.stream():
            tickers.extend(doc.to_dict().get('tickers', []))

        # Filter out the ticker to remove
        updated_tickers = [ticker for ticker in tickers if ticker['ticker'] != ticker_to_remove]

        # Update the user's collection with the updated tickers
        for doc in user_collection_ref.stream():
            doc.reference.update({'tickers': updated_tickers})

        logging.debug(f"Removed ticker {ticker_to_remove} for user_id {user_id}")
        return jsonify({'message': 'Ticker removed successfully'}), 200
    except Exception as e:
        logging.error(f"Error removing ticker: {e}")
        return jsonify({'error': str(e)}), 500