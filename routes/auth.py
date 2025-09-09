# routes/auth.py
import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)

def _is_logged_in() -> bool:
    return session.get("is_admin") is True

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not _is_logged_in():
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if _is_logged_in():
        return redirect(request.args.get("next") or "/")

    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_hash = os.getenv("ADMIN_PASSWORD_HASH")
        admin_plain = os.getenv("ADMIN_PASSWORD") if not admin_hash else None

        valid_user = (username == admin_user)
        valid_pass = False

        if admin_hash:
            try:
                valid_pass = check_password_hash(admin_hash, password)
            except Exception:
                valid_pass = False
        elif admin_plain is not None:
            valid_pass = (password == admin_plain)

        if valid_user and valid_pass:
            session.clear()
            session["is_admin"] = True
            session["admin_username"] = admin_user
            session.permanent = True
            return redirect(request.args.get("next") or "/")
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template("login.html", error=error)

@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
