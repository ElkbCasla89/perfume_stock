from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from models import get_db
import re

bp = Blueprint("sql", __name__, url_prefix="/sql")

def _is_select(sql: str) -> bool:
    return re.match(r'^\s*SELECT\b', sql, re.I) is not None

@bp.get("/")
def sql_page():
    enabled = bool(current_app.config.get("SQL_CONSOLE_TOKEN"))
    return render_template("sql.html", title="SQL", enabled=enabled)

@bp.post("/run")
def sql_run():
    token_expected = current_app.config.get("SQL_CONSOLE_TOKEN")
    token = (request.form.get("token") or "").strip()
    if not token_expected or token != token_expected:
        flash("Acceso denegado. Configurá SQL_CONSOLE_TOKEN y pasá el token correcto.", "err")
        return redirect(url_for("sql.sql_page"))

    db = get_db()
    sql = (request.form.get("sql") or "").strip()
    if not sql:
        flash("Ingresá una consulta.", "err")
        return redirect(url_for("sql.sql_page"))

    try:
        # SELECT simple → mostramos tabla. Todo lo demás → executescript + commit.
        if _is_select(sql) and ";" not in sql.strip().rstrip(";"):
            rows = db.execute(sql).fetchall()
            cols = list(rows[0].keys()) if rows else []
            data = [dict(r) for r in rows]
            return render_template("sql.html", title="SQL", enabled=True,
                                   sql=sql, result={"columns": cols, "rows": data, "rowcount": len(data)})
        else:
            db.executescript(sql)
            db.commit()
            flash("Script ejecutado correctamente.", "ok")
            return render_template("sql.html", title="SQL", enabled=True, sql=sql, result=None)
    except Exception as e:
        flash(f"Error: {e}", "err")
        return render_template("sql.html", title="SQL", enabled=True, sql=sql, result=None)
