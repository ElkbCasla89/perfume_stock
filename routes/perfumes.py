from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import get_db, q_brands, q_types, q_sizes, q_perfume_list
import sqlite3

bp = Blueprint("perfumes", __name__)

def _to_cents(s):
    # acepta "1234.56" o "1234,56"
    s = (s or "").replace(".", "").replace(",", ".") if "," in (s or "") else (s or "")
    try:
        return int(round(float(s) * 100))
    except Exception:
        return 0

@bp.route("/perfumes")
def perfumes_page():
    db = get_db()
    recent = q_perfume_list(db, limit=20)
    return render_template(
        "perfumes.html",
        title="Stock de Perfumes • Perfumes",
        brands=q_brands(db),
        types=q_types(db),
        sizes=q_sizes(db),
        perfumes=recent,
    )

@bp.route("/perfume/add", methods=["POST"])
def perfume_add():
    db = get_db()
    try:
        brand_id = int(request.form["brand_id"])
        type_id = int(request.form["type_id"])
        size_id = int(request.form["size_id"])
        name = request.form["name"].strip()
        barcode = request.form.get("barcode", "").strip() or None
        quantity = int(request.form["quantity"])
        price_cents = _to_cents(request.form.get("price"))

        if quantity < 0:
            raise ValueError("Cantidad negativa")

        db.execute(
            "INSERT INTO perfumes (brand_id, type_id, size_id, name, barcode, quantity, price_cents) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (brand_id, type_id, size_id, name, barcode, quantity, price_cents),
        )
        db.commit()
        flash("Perfume creado correctamente.", "ok")
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: perfumes.barcode" in str(e):
            flash("El código de barras ya existe.", "err")
        else:
            flash("Error de integridad al crear el perfume.", "err")
    except Exception as e:
        flash(f"Error: {e}", "err")
    return redirect(url_for("perfumes.perfumes_page"))
