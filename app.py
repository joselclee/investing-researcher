from flask import Flask
from endpoints.optimize_portfolio import optimize_portfolio_bp
from endpoints.monte_carlo_var import monte_carlo_var_bp

app = Flask(__name__)

app.register_blueprint(optimize_portfolio_bp)
app.register_blueprint(monte_carlo_var_bp)

if __name__ == '__main__':
    app.run(debug=True)