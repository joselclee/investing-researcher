# endpoints/add_tickers.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from firebase_config import db
import logging

logging.basicConfig(level=logging.DEBUG)

add_tickers_bp = Blueprint('add_tickers', __name__)

@add_tickers_bp.route('/api/v1/add-tickers', methods=['POST'])
@cross_origin()
def add_tickers():
    data = request.json
    logging.debug(f"Received data: {data}")
    user_id = data.get('user_id')
    tickers = data.get('tickers')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    if not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be a list'}), 400

    for ticker in tickers:
        if not isinstance(ticker, dict) or 'ticker' not in ticker or 'value' not in ticker:
            return jsonify({'error': 'Each ticker must be an object with "ticker" and "value"'}), 400

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
            existing_tickers = existing_data.get('tickers', [])
            existing_tickers.extend(tickers)
            doc_ref.update({'tickers': existing_tickers})
        else:
            # Create a new document if none exists
            user_collection_ref.add({'user_id': user_id, 'tickers': tickers})

        logging.debug(f"Tickers added for user_id {user_id}: {tickers}")
        return jsonify({'message': 'Tickers added successfully'}), 200
    except Exception as e:
        logging.error(f"Error adding tickers: {e}")
        return jsonify({'error': str(e)}), 500