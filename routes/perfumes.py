from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import get_db, q_brands, q_types, q_sizes, q_perfume_list
import sqlite3

bp = Blueprint("perfumes", __name__)

def _to_cents(s):
    s = (s or "").strip()
    s = s.replace(".", "").replace(",", ".") if "," in s else s
    try:
        return int(round(float(s) * 100))
    except Exception:
        return 0

@bp.route("/perfumes")
def perfumes_page():
    db = get_db()
    recent = q_perfume_list(db, limit=50)
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
        initial_qty = int(request.form.get("quantity", 0))
        price_cents = _to_cents(request.form.get("price"))

        # 1) Creamos el perfume con cantidad 0 para mantener historial consistente
        # Intentamos RETURNING id (PG/SQLite moderno); si no, pedimos last_insert_rowid()
        try:
            row = db.execute(
                "INSERT INTO perfumes (brand_id, type_id, size_id, name, barcode, quantity, price_cents) "
                "VALUES (?, ?, ?, ?, ?, 0, ?) RETURNING id",
                (brand_id, type_id, size_id, name, barcode, price_cents)
            ).fetchone()
            perfume_id = (row and row.get("id")) or None
        except Exception:
            db.execute(
                "INSERT INTO perfumes (brand_id, type_id, size_id, name, barcode, quantity, price_cents) "
                "VALUES (?, ?, ?, ?, ?, 0, ?)",
                (brand_id, type_id, size_id, name, barcode, price_cents)
            )
            # SQLite
            try:
                perfume_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            except Exception:
                # Fallback (no debería pasar)
                perfume_id = db.execute(
                    "SELECT id FROM perfumes WHERE brand_id=? AND type_id=? AND size_id=? AND name=? "
                    "ORDER BY id DESC LIMIT 1",
                    (brand_id, type_id, size_id, name)
                ).fetchone()["id"]

        # 2) Si vino cantidad inicial > 0, la aplicamos como movimiento
        if initial_qty > 0:
            db.execute("UPDATE perfumes SET quantity = ? WHERE id=?", (initial_qty, perfume_id))
            db.execute(
                "INSERT INTO stock_moves (perfume_id, delta, reason) VALUES (?, ?, ?)",
                (perfume_id, initial_qty, "Alta inicial")
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

@bp.route("/perfume/update", methods=["POST"])
def perfume_update():
    db = get_db()
    try:
        pid = int(request.form["id"])
        brand_id = int(request.form["brand_id"])
        type_id = int(request.form["type_id"])
        size_id = int(request.form["size_id"])
        name = request.form["name"].strip()
        barcode = request.form.get("barcode", "").strip() or None
        price_cents = _to_cents(request.form.get("price"))
        new_qty = int(request.form.get("quantity", 0))

        # Traemos cantidad actual para registrar ajuste si cambia
        current = db.execute("SELECT quantity FROM perfumes WHERE id=?", (pid,)).fetchone()
        if not current:
            raise ValueError("Perfume inexistente.")
        old_qty = int(current["quantity"])
        delta = new_qty - old_qty

        with db:
            db.execute(
                "UPDATE perfumes SET brand_id=?, type_id=?, size_id=?, name=?, barcode=?, price_cents=?, quantity=? "
                "WHERE id=?",
                (brand_id, type_id, size_id, name, barcode, price_cents, new_qty, pid)
            )
            if delta != 0:
                reason = "Ajuste manual (edición)"
                db.execute(
                    "INSERT INTO stock_moves (perfume_id, delta, reason) VALUES (?, ?, ?)",
                    (pid, delta, reason)
                )

        flash("Perfume actualizado.", "ok")
    except Exception as e:
        flash(f"Error al actualizar perfume: {e}", "err")
    return redirect(url_for("perfumes.perfumes_page"))
