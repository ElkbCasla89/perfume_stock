from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import get_db, q_clients

bp = Blueprint("clients", __name__, url_prefix="/clients")

@bp.route("/")
def clients_page():
    db = get_db()
    return render_template("clients.html", title="Clientes", clients=q_clients(db))

@bp.route("/add", methods=["POST"])
def clients_add():
    db = get_db()
    f = request.form
    db.execute(
        "INSERT INTO clients (first_name, last_name, nickname, phone, email, address) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (f["first_name"], f["last_name"], f.get("nickname") or None, f.get("phone"),
         f.get("email"), f.get("address"))
    )
    db.commit()
    flash("Cliente creado.", "ok")
    return redirect(url_for("clients.clients_page"))

@bp.route("/update", methods=["POST"])
def clients_update():
    db = get_db()
    f = request.form
    db.execute(
        "UPDATE clients SET first_name=?, last_name=?, nickname=?, phone=?, email=?, address=? WHERE id=?",
        (f["first_name"], f["last_name"], f.get("nickname") or None, f.get("phone"),
         f.get("email"), f.get("address"), int(f["id"]))
    )
    db.commit()
    flash("Cliente actualizado.", "ok")
    return redirect(url_for("clients.clients_page"))
