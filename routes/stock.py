from flask import Blueprint, render_template, request, redirect, url_for, flash, request as flask_request
from models import get_db, q_perfume_list, q_clients

bp = Blueprint("stock", __name__)

def _to_cents(s):
    s = (s or "").replace(".", "").replace(",", ".") if "," in (s or "") else (s or "")
    try:
        return int(round(float(s) * 100))
    except Exception:
        return None

@bp.route("/stock")
def stock_page():
    db = get_db()
    perfumes = q_perfume_list(db)
    clients = q_clients(db)
    return render_template(
        "stock.html",
        title="Stock de Perfumes • Stock",
        perfumes=perfumes,
        clients=clients
    )

@bp.route("/stock/move", methods=["POST"])
def stock_move():
    db = get_db()
    try:
        perfume_id = int(request.form["perfume_id"])
        amount = int(request.form["amount"])
        op = request.form["op"]
        reason = request.form.get("reason", "").strip() or None
        customer_id = request.form.get("customer_id") or None
        price_override = request.form.get("unit_price")

        if amount <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        delta = amount if op == "add" else -amount

        cur = db.execute("SELECT quantity, name, price_cents FROM perfumes WHERE id=?", (perfume_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Perfume inexistente.")

        unit_price_cents = None
        if delta < 0:
            # venta: usar override si vino, sino el precio del perfume
            override_cents = _to_cents(price_override)
            unit_price_cents = override_cents if override_cents is not None and override_cents >= 0 else row["price_cents"]

        new_qty = row["quantity"] + delta
        if new_qty < 0:
            raise ValueError(f"No se puede dejar stock negativo (actual: {row['quantity']}, resta: {amount}).")

        with db:
            db.execute("UPDATE perfumes SET quantity = quantity + ? WHERE id=?", (delta, perfume_id))
            db.execute(
                "INSERT INTO stock_moves (perfume_id, delta, reason, customer_id, unit_price_cents) "
                "VALUES (?,?,?,?,?)",
                (perfume_id, delta, reason, customer_id, unit_price_cents)
            )

        extra = ""
        if delta < 0:
            total = (unit_price_cents or 0) * amount
            extra = f" (venta: {amount} x {unit_price_cents/100:,.2f} = ${total/100:,.2f})"
            if customer_id:
                c = db.execute("SELECT first_name, last_name FROM clients WHERE id=?", (customer_id,)).fetchone()
                if c:
                    extra += f" a <b>{c['first_name']} {c['last_name']}</b>"
        flash(f"Movimiento aplicado a <b>{row['name']}</b>. Nuevo stock: <b>{new_qty}</b>.{extra}", "ok")
    except Exception as e:
        flash(f"Error al mover stock: {e}", "err")
    ref = flask_request.referrer or url_for('catalog.catalog')
    return redirect(ref)
