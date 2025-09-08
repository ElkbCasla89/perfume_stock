from flask import Blueprint, render_template
from models import get_db, q_stock_by_brand, q_top_sold_perfumes

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@bp.route("/")
def dashboard_page():
    db = get_db()
    stock_by_brand = q_stock_by_brand(db)
    top_sold = q_top_sold_perfumes(db, limit=5)
    return render_template(
        "dashboard.html",
        title="Stock de Perfumes • Dashboard",
        stock_by_brand=stock_by_brand,
        top_sold=top_sold
    )
