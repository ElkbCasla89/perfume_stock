from flask import Blueprint, render_template, request
from models import get_db, q_perfume_list

bp = Blueprint("moves", __name__)

@bp.route("/moves")
def moves_page():
    db = get_db()
    perfume_id = request.args.get("perfume_id")
    limit = int(request.args.get("limit", 50))
    sql = (
        "SELECT m.id, m.delta, m.reason, m.created_at, m.unit_price_cents, "
        "p.name, b.name AS brand, t.name AS type, s.ml, "
        "c.first_name, c.last_name, c.nickname "
        "FROM stock_moves m "
        "JOIN perfumes p ON p.id=m.perfume_id "
        "JOIN brands b ON b.id=p.brand_id "
        "JOIN perfume_types t ON t.id=p.type_id "
        "JOIN sizes s ON s.id=p.size_id "
        "LEFT JOIN clients c ON c.id=m.customer_id "
    )
    params = []
    if perfume_id:
        sql += "WHERE p.id=? "
        params.append(perfume_id)
    sql += "ORDER BY m.id DESC LIMIT ?"
    params.append(limit)

    data = db.execute(sql, params).fetchall()
    return render_template(
        "moves.html",
        title="Stock de Perfumes • Movimientos",
        perfumes=q_perfume_list(db),
        moves=data
    )
