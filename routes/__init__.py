from . import catalog, perfumes, stock, admin, moves, dashboard, clients

def register_blueprints(app):
    app.register_blueprint(catalog.bp)
    app.register_blueprint(perfumes.bp)
    app.register_blueprint(stock.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(moves.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(clients.bp)
