# test_add_tickers.py
import requests
import json

url = "http://127.0.0.1:5000/api/v1/add-tickers"

# Sample payload
payload = {
    "user_id": "test_user",
    "tickers": [
        {"ticker": "AAPL", "value": 150.0},
        {"ticker": "GOOGL", "value": 2800.0}
    ]
}

headers = {
    "Content-Type": "application/json"
}

def test_add_tickers():
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

if __name__ == "__main__":
    test_add_tickers()