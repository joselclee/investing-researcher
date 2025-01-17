from flask import Flask
from endpoints.optimize_portfolio import optimize_portfolio_bp
from endpoints.monte_carlo_var import monte_carlo_var_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(optimize_portfolio_bp)
app.register_blueprint(monte_carlo_var_bp)

if __name__ == '__main__':
    app.run(debug=True)