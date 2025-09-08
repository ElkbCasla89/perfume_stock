from flask import Flask, redirect, url_for
from config import Config
from models import init_db, close_db
from routes import register_blueprints

def _money_filter(value):
    try:
        cents = int(value or 0)
        return f"${cents/100:,.2f}"
    except Exception:
        return "$0.00"

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    register_blueprints(app)

    @app.before_request
    def _ensure_db():
        init_db()

    @app.teardown_appcontext
    def _close_db(exc):
        close_db(exc)

    @app.route("/")
    def index():
        return redirect(url_for("dashboard.dashboard_page"))

    # utilidades Jinja
    app.jinja_env.globals.update(str=str)
    app.jinja_env.filters["money"] = _money_filter

    return app

if __name__ == "__main__":
    app = create_app()
    print("Iniciando Stock de Perfumes en http://127.0.0.1:5000")
    app.run(debug=app.config["DEBUG"])
