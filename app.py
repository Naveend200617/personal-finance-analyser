from flask import Flask, render_template, redirect, url_for
from config import config_by_name
from extensions import db, migrate, csrf
import os


def create_app(config_name=None):
    app = Flask(__name__)
    cfg = config_name or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config_by_name.get(cfg, config_by_name["default"]))

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # ---- Blueprints ----
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.income import income_bp
    from routes.expenses import expenses_bp
    from routes.transactions import transactions_bp
    from routes.budgets import budgets_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(reports_bp)

    # ---- Landing page / index ----
    @app.route("/")
    def home():
        return render_template("index.html")

    # Profile page is part of dashboard area — keep it simple here.
    from routes.helpers import login_required
    from flask import session

    @app.route("/profile")
    @login_required
    def profile():
        from models import User, Transaction
        from flask import session as s
        user = User.query.get_or_404(s["user_id"])
        txn_count = Transaction.query.filter_by(user_id=user.id).count()
        return render_template("profile.html", user=user, txn_count=txn_count)

    # ---- Error handlers ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Jinja filter for INR formatting
    @app.template_filter("inr")
    def inr(value):
        try:
            return "₹{:,.2f}".format(float(value))
        except (ValueError, TypeError):
            return "₹0.00"

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
