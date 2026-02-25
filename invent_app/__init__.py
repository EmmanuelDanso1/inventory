from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes import main, items, categories, suppliers, transactions, reports, api
    
    app.register_blueprint(main.bp)
    app.register_blueprint(items.bp, url_prefix='/items')
    app.register_blueprint(categories.bp, url_prefix='/categories')
    app.register_blueprint(suppliers.bp, url_prefix='/suppliers')
    app.register_blueprint(transactions.bp, url_prefix='/transactions')
    app.register_blueprint(reports.bp, url_prefix='/reports')
    app.register_blueprint(api.bp, url_prefix='/api')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app