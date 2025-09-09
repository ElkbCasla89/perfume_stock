# routes/__init__.py
import os
from datetime import timedelta
from flask import request, redirect, url_for, session

from . import catalog, perfumes, stock, admin, moves, dashboard, clients
from .auth import auth_bp  # NUEVO

def _ensure_session_defaults(app):
    # No pisa valores existentes; solo setea por defecto si faltan
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-change-me"))
    app.config.setdefault("PERMANENT_SESSION_LIFETIME", timedelta(hours=12))
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault(
        "SESSION_COOKIE_SECURE",
        bool(os.getenv("RENDER") or os.getenv("FLASK_ENV") == "production")
    )

def _attach_global_login_guard(app):
    @app.before_request
    def _require_login_globally():
        open_endpoints = {"auth.login", "auth.logout"}
        if request.endpoint in open_endpoints:
            return None
        if request.path.startswith("/static") or request.path == "/favicon.ico":
            return None
        if not session.get("is_admin"):
            return redirect(url_for("auth.login", next=request.path))
        return None

def register_blueprints(app):
    _ensure_session_defaults(app)     # asegura SECRET_KEY/cookies
    app.register_blueprint(auth_bp)   # registrar /login antes que el guard

    # Tus blueprints existentes
    app.register_blueprint(catalog.bp)
    app.register_blueprint(perfumes.bp)
    app.register_blueprint(stock.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(moves.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(clients.bp)

    _attach_global_login_guard(app)   # protege TODO el sitio
