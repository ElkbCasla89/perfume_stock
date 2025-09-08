from flask import Blueprint, render_template, request, make_response, current_app
from models import get_db, q_brands, q_types, q_sizes, q_perfume_list
import csv
import io
from datetime import datetime

bp = Blueprint("catalog", __name__, url_prefix="/catalog")

def _collect_filters(req):
    return {
        "brand_id": req.args.get("brand_id") or None,
        "type_id": req.args.get("type_id") or None,
        "size_id": req.args.get("size_id") or None,
        "q": req.args.get("q") or None,
        "barcode": req.args.get("barcode") or None,
        "min_qty": int(req.args.get("min_qty")) if req.args.get("min_qty") else None,
        "max_qty": int(req.args.get("max_qty")) if req.args.get("max_qty") else None,
    }

@bp.route("/")
def catalog():
    db = get_db()
    filters = _collect_filters(request)
    perfumes = q_perfume_list(db, filters)
    return render_template(
        "catalog.html",
        title="Stock de Perfumes • Catálogo",
        brands=q_brands(db),
        types=q_types(db),
        sizes=q_sizes(db),
        perfumes=perfumes,
        low_threshold=current_app.config["LOW_STOCK_THRESHOLD"]
    )

@bp.route("/export", methods=["GET", "POST"])
def export_csv():
    db = get_db()
    source = request.form if request.method == "POST" else request.args
    filters = {
        "brand_id": source.get("brand_id") or None,
        "type_id": source.get("type_id") or None,
        "size_id": source.get("size_id") or None,
        "q": source.get("q") or None,
        "barcode": source.get("barcode") or None,
        "min_qty": int(source.get("min_qty")) if source.get("min_qty") else None,
        "max_qty": int(source.get("max_qty")) if source.get("max_qty") else None,
    }
    rows = q_perfume_list(db, filters)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Marca", "Tipo", "Nombre", "Tamaño_ml", "Código_de_barras", "Precio", "Stock", "Creado"])
    for r in rows:
        writer.writerow([
            r["brand"], r["type"], r["name"], r["ml"], r["barcode"] or "",
            f"{r['price_cents']/100:.2f}", r["quantity"], r["created_at"]
        ])
    csv_data = output.getvalue()
    output.close()

    fname = f"catalogo_perfumes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    resp = make_response(csv_data)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{fname}"'
    return resp
