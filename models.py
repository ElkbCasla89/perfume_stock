import os
import sqlite3
from flask import g, current_app

# ========= Conexiones =========

def _connect_sqlite(path: str):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _connect_postgres(dsn: str):
    # Se importa acá para no requerir psycopg2 en local si no hace falta
    import psycopg2
    import psycopg2.extras

    class _PgCursorAdapter:
        def __init__(self, cur): self._cur = cur
        def fetchall(self): return self._cur.fetchall()
        def fetchone(self): return self._cur.fetchone()

    class _PgConnAdapter:
        def __init__(self, conn): self.conn = conn
        def execute(self, sql, params=()):
            # Cambiamos placeholders SQLite (?) -> Postgres (%s) si hace falta
            if "%s" not in sql:
                sql = "%s".join(sql.split("?"))
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params or ())
            return _PgCursorAdapter(cur)
        def executescript(self, script: str):
            with self.conn:
                cur = self.conn.cursor()
                for stmt in script.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        cur.execute(stmt)
        def commit(self): self.conn.commit()
        def close(self): self.conn.close()

    return _PgConnAdapter(psycopg2.connect(dsn))

def get_db():
    """Devuelve la conexión activa y setea g.db_kind = 'pg' | 'sqlite'."""
    if "db" not in g:
        durl = os.environ.get("DATABASE_URL")
        if durl:
            # Si hay DATABASE_URL, usamos Postgres sí o sí (persistente en Render)
            g.db = _connect_postgres(durl)
            g.db_kind = "pg"
        else:
            g.db = _connect_sqlite(current_app.config["DB_PATH"])
            g.db_kind = "sqlite"
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        close_fn = getattr(db, "close", None)
        if callable(close_fn):
            close_fn()

# ========= Inicialización / Migraciones =========

def init_db():
    db = get_db()
    kind = getattr(g, "db_kind", "sqlite")
    if kind == "sqlite":
        _init_sqlite(db)
    else:
        _init_postgres(db)

def _init_sqlite(db):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS brands (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS perfume_types (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS sizes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ml INTEGER NOT NULL UNIQUE CHECK (ml > 0)
        );
        CREATE TABLE IF NOT EXISTS clients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          first_name TEXT NOT NULL,
          last_name  TEXT NOT NULL,
          nickname   TEXT,
          phone      TEXT,
          email      TEXT,
          address    TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS perfumes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          brand_id INTEGER NOT NULL,
          type_id INTEGER NOT NULL,
          size_id INTEGER NOT NULL,
          name TEXT NOT NULL,
          barcode TEXT UNIQUE,
          quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
          price_cents INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE RESTRICT,
          FOREIGN KEY (type_id) REFERENCES perfume_types(id) ON DELETE RESTRICT,
          FOREIGN KEY (size_id) REFERENCES sizes(id) ON DELETE RESTRICT
        );
        CREATE INDEX IF NOT EXISTS idx_perfumes_name ON perfumes(name);
        CREATE INDEX IF NOT EXISTS idx_perfumes_brand ON perfumes(brand_id);
        CREATE INDEX IF NOT EXISTS idx_perfumes_type ON perfumes(type_id);
        CREATE INDEX IF NOT EXISTS idx_perfumes_size ON perfumes(size_id);
        CREATE INDEX IF NOT EXISTS idx_perfumes_barcode ON perfumes(barcode);

        CREATE TABLE IF NOT EXISTS stock_moves (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          perfume_id INTEGER NOT NULL,
          delta INTEGER NOT NULL,
          reason TEXT,
          customer_id INTEGER,
          unit_price_cents INTEGER,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (perfume_id) REFERENCES perfumes(id) ON DELETE CASCADE,
          FOREIGN KEY (customer_id) REFERENCES clients(id) ON DELETE SET NULL
        );
        """
    )
    # Migraciones suaves (ignoran si ya existen)
    for ddl in [
        "ALTER TABLE perfumes ADD COLUMN price_cents INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE stock_moves ADD COLUMN customer_id INTEGER;",
        "ALTER TABLE stock_moves ADD COLUMN unit_price_cents INTEGER;"
    ]:
        try:
            db.execute(ddl); db.commit()
        except Exception:
            pass

def _init_postgres(db):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS brands (
          id SERIAL PRIMARY KEY,
          name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS perfume_types (
          id SERIAL PRIMARY KEY,
          name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS sizes (
          id SERIAL PRIMARY KEY,
          ml INTEGER NOT NULL UNIQUE CHECK (ml > 0)
        );
        CREATE TABLE IF NOT EXISTS clients (
          id SERIAL PRIMARY KEY,
          first_name TEXT NOT NULL,
          last_name  TEXT NOT NULL,
          nickname   TEXT,
          phone      TEXT,
          email      TEXT,
          address    TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS perfumes (
          id SERIAL PRIMARY KEY,
          brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE RESTRICT,
          type_id  INTEGER NOT NULL REFERENCES perfume_types(id) ON DELETE RESTRICT,
          size_id  INTEGER NOT NULL REFERENCES sizes(id) ON DELETE RESTRICT,
          name TEXT NOT NULL,
          barcode TEXT UNIQUE,
          quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
          price_cents INTEGER NOT NULL DEFAULT 0,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_perfumes_name ON perfumes(name);
        CREATE INDEX IF NOT EXISTS idx_perfumes_brand ON perfumes(brand_id);
        CREATE INDEX IF NOT EXISTS idx_perfumes_type ON perfumes(type_id);
        CREATE INDEX IF NOT EXISTS idx_perfumes_size ON perfumes(size_id);
        CREATE INDEX IF NOT EXISTS idx_perfumes_barcode ON perfumes(barcode);

        CREATE TABLE IF NOT EXISTS stock_moves (
          id SERIAL PRIMARY KEY,
          perfume_id INTEGER NOT NULL REFERENCES perfumes(id) ON DELETE CASCADE,
          delta INTEGER NOT NULL,
          reason TEXT,
          customer_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
          unit_price_cents INTEGER,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    for ddl in [
        "ALTER TABLE perfumes ADD COLUMN price_cents INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE stock_moves ADD COLUMN customer_id INTEGER REFERENCES clients(id) ON DELETE SET NULL",
        "ALTER TABLE stock_moves ADD COLUMN unit_price_cents INTEGER"
    ]:
        try:
            db.execute(ddl); db.commit()
        except Exception:
            pass

# ========= Queries =========

def q_brands(db):
    return db.execute(
        "SELECT b.id, b.name, "
        "(SELECT COUNT(1) FROM perfumes p WHERE p.brand_id=b.id) AS perf_count "
        "FROM brands b ORDER BY b.name"
    ).fetchall()

def q_types(db):
    return db.execute(
        "SELECT t.id, t.name, "
        "(SELECT COUNT(1) FROM perfumes p WHERE p.type_id=t.id) AS perf_count "
        "FROM perfume_types t ORDER BY t.name"
    ).fetchall()

def q_sizes(db):
    return db.execute(
        "SELECT s.id, s.ml, "
        "(SELECT COUNT(1) FROM perfumes p WHERE p.size_id=s.id) AS perf_count "
        "FROM sizes s ORDER BY s.ml"
    ).fetchall()

def q_perfume_list(db, filters=None, limit=None):
    where = []
    params = []
    if filters:
        if filters.get("brand_id"):
            where.append("p.brand_id = ?"); params.append(filters["brand_id"])
        if filters.get("type_id"):
            where.append("p.type_id = ?"); params.append(filters["type_id"])
        if filters.get("size_id"):
            where.append("p.size_id = ?"); params.append(filters["size_id"])
        if filters.get("q"):
            where.append("LOWER(p.name) LIKE ?"); params.append(f"%{filters['q'].lower()}%")
        if filters.get("barcode"):
            where.append("p.barcode IS NOT NULL AND p.barcode LIKE ?"); params.append(f"%{filters['barcode']}%")
        if filters.get("min_qty") is not None:
            where.append("p.quantity >= ?"); params.append(filters["min_qty"])
        if filters.get("max_qty") is not None:
            where.append("p.quantity <= ?"); params.append(filters["max_qty"])

    sql = (
        "SELECT p.id, p.name, p.barcode, p.quantity, p.price_cents, p.created_at, "
        "b.name AS brand, t.name AS type, s.ml "
        "FROM perfumes p "
        "JOIN brands b ON b.id=p.brand_id "
        "JOIN perfume_types t ON t.id=p.type_id "
        "JOIN sizes s ON s.id=p.size_id "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY b.name, t.name, p.name"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db.execute(sql, params).fetchall()

def q_clients(db):
    return db.execute(
        "SELECT id, first_name, last_name, nickname, phone, email, address, created_at "
        "FROM clients ORDER BY last_name, first_name"
    ).fetchall()

def q_stock_by_brand(db):
    return db.execute(
        "SELECT b.name AS brand, SUM(p.quantity) AS qty "
        "FROM perfumes p JOIN brands b ON b.id=p.brand_id "
        "GROUP BY b.name ORDER BY qty DESC"
    ).fetchall()

def q_top_sold_perfumes(db, limit=5):
    return db.execute(
        "SELECT p.name AS perfume, b.name AS brand, s.ml AS ml, "
        "SUM(CASE WHEN m.delta < 0 THEN -m.delta ELSE 0 END) AS sold_qty "
        "FROM stock_moves m "
        "JOIN perfumes p ON p.id=m.perfume_id "
        "JOIN brands b ON b.id=p.brand_id "
        "JOIN sizes s ON s.id=p.size_id "
        "GROUP BY p.id "
        "ORDER BY sold_qty DESC LIMIT ?",
        (limit,)
    ).fetchall()
