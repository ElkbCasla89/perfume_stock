from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import get_db, q_brands, q_types, q_sizes
import sqlite3

bp = Blueprint("admin", __name__)

@bp.route("/admin")
def admin_page():
    db = get_db()
    return render_template(
        "admin.html",
        title="Stock de Perfumes • Admin",
        brands=q_brands(db),
        types=q_types(db),
        sizes=q_sizes(db),
    )

@bp.route("/brand/add", methods=["POST"])
def brand_add():
    name = request.form["name"].strip()
    db = get_db()
    try:
        db.execute("INSERT INTO brands (name) VALUES (?)", (name,))
        db.commit()
        flash("Marca agregada.", "ok")
    except sqlite3.IntegrityError:
        flash("La marca ya existe.", "warn")
    return redirect(url_for("admin.admin_page"))

@bp.route("/type/add", methods=["POST"])
def type_add():
    name = request.form["name"].strip()
    db = get_db()
    try:
        db.execute("INSERT INTO perfume_types (name) VALUES (?)", (name,))
        db.commit()
        flash("Tipo de perfume agregado.", "ok")
    except sqlite3.IntegrityError:
        flash("El tipo ya existe.", "warn")
    return redirect(url_for("admin.admin_page"))

@bp.route("/size/add", methods=["POST"])
def size_add():
    ml = int(request.form["ml"])
    db = get_db()
    try:
        db.execute("INSERT INTO sizes (ml) VALUES (?)", (ml,))
        db.commit()
        flash("Tamaño agregado.", "ok")
    except sqlite3.IntegrityError:
        flash("Ese tamaño ya existe.", "warn")
    return redirect(url_for("admin.admin_page"))
