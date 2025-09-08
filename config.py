import os

class Config:
    SECRET_KEY = "cambia-esta-clave-si-vas-a-publicar"
    BASE_DIR = os.path.dirname(__file__)
    DB_PATH = os.path.join(BASE_DIR, "perfumes.db")
    SQL_CONSOLE_TOKEN = os.environ.get("SQL_CONSOLE_TOKEN")
    DEBUG = True

    # ⚠️ Umbral de stock bajo
    LOW_STOCK_THRESHOLD = 1
