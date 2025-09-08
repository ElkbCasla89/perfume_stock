from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import get_db, q_clients
import sqlite3

bp = Blueprint("clients", __name__)

@bp.route("/clients")
def clients_page():
    db = get_db()
    return render_template(
        "clients.html",
        title="Stock de Perfumes • Clientes",
        clients=q_clients(db)
    )

@bp.route("/client/add", methods=["POST"])
def client_add():
    db = get_db()
    try:
        data = {
            "first_name": request.form["first_name"].strip(),
            "last_name": request.form["last_name"].strip(),
            "nickname": request.form.get("nickname", "").strip() or None,
            "phone": request.form.get("phone", "").strip() or None,
            "email": request.form.get("email", "").strip() or None,
            "address": request.form.get("address", "").strip() or None,
        }
        db.execute(
            "INSERT INTO clients (first_name, last_name, nickname, phone, email, address) "
            "VALUES (?,?,?,?,?,?)",
            (data["first_name"], data["last_name"], data["nickname"],
             data["phone"], data["email"], data["address"])
        )
        db.commit()
        flash("Cliente agregado.", "ok")
    except sqlite3.IntegrityError as e:
        flash(f"Error de integridad: {e}", "err")
    except Exception as e:
        flash(f"Error: {e}", "err")
    return redirect(url_for("clients.clients_page"))
