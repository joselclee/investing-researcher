# app.py
from flask import Flask
from endpoints.optimize_portfolio import optimize_portfolio_bp
from endpoints.monte_carlo_var import monte_carlo_var_bp
from endpoints.add_tickers import add_tickers_bp
from endpoints.get_tickers import get_tickers_bp
from endpoints.remove_ticker import remove_ticker_bp
from endpoints.update_ticker_value import update_ticker_value_bp
from endpoints.account import account_bp
from endpoints.day_history import day_history_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(optimize_portfolio_bp)
app.register_blueprint(monte_carlo_var_bp)
app.register_blueprint(add_tickers_bp)
app.register_blueprint(get_tickers_bp)
app.register_blueprint(remove_ticker_bp)
app.register_blueprint(update_ticker_value_bp)
app.register_blueprint(account_bp)
app.register_blueprint(day_history_bp)

if __name__ == '__main__':
    app.run(debug=True)