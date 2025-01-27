# endpoints/update_ticker_value.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from firebase_config import db
import logging

logging.basicConfig(level=logging.DEBUG)

update_ticker_value_bp = Blueprint('update_ticker_value', __name__)

@update_ticker_value_bp.route('/api/v1/update-ticker-value', methods=['PUT'])
@cross_origin()
def update_ticker_value():
    data = request.json
    logging.debug(f"Received data: {data}")
    user_id = data.get('user_id')
    ticker_to_update = data.get('ticker')
    new_value = data.get('value')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    if not ticker_to_update:
        return jsonify({'error': 'Ticker is required'}), 400

    if new_value is None:
        return jsonify({'error': 'New value is required'}), 400

    try:
        # Access the user's collection
        user_collection_ref = db.collection(f'portfolios_{user_id}')
        docs = user_collection_ref.stream()
        doc_id = None

        # Check if a document already exists
        for doc in docs:
            doc_id = doc.id
            break

        if doc_id:
            # Update the existing document
            doc_ref = user_collection_ref.document(doc_id)
            existing_data = doc_ref.get().to_dict()
            tickers = existing_data.get('tickers', [])

            # Update the value for the specified ticker
            ticker_found = False
            for ticker in tickers:
                if ticker['ticker'] == ticker_to_update:
                    ticker_found = True
                    if new_value == 0:
                        tickers.remove(ticker)
                    else:
                        ticker['value'] = new_value
                    break

            if not ticker_found:
                return jsonify({'error': 'Ticker not found'}), 404

            doc_ref.update({'tickers': tickers})
            logging.debug(f"Updated ticker {ticker_to_update} for user_id {user_id} with new value {new_value}")
            return jsonify({'message': 'Ticker value updated successfully'}), 200
        else:
            return jsonify({'error': 'No document found for the user'}), 404
    except Exception as e:
        logging.error(f"Error updating ticker value: {e}")
        return jsonify({'error': str(e)}), 500