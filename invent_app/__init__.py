"""
Flask Application Factory
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name='default'):
    """
    Application factory pattern
    Creates and configures the Flask application
    
    Args:
        config_name: Configuration to use (default, development, production, testing)
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register shell context
    register_shell_context(app)
    
    return app


def register_blueprints(app):
    """Register all Flask blueprints"""
    from app.routes.main import bp as main_bp
    from app.routes.items import bp as items_bp
    from app.routes.categories import bp as categories_bp
    from app.routes.suppliers import bp as suppliers_bp
    from app.routes.transactions import bp as transactions_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.api import bp as api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(items_bp, url_prefix='/items')
    app.register_blueprint(categories_bp, url_prefix='/categories')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')


def register_error_handlers(app):
    """Register error handlers for common HTTP errors"""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        db.session.rollback()  # Rollback any failed transactions
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        return render_template('errors/403.html'), 403


def register_template_filters(app):
    """Register custom Jinja2 template filters"""
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Format number as currency"""
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"
    
    @app.template_filter('number')
    def number_filter(value):
        """Format number with thousands separator"""
        if value is None:
            return "0"
        return f"{value:,}"
    
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        """Format datetime object"""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('stock_status')
    def stock_status_filter(item):
        """Get stock status badge class"""
        if item.current_stock == 0:
            return 'danger'
        elif item.current_stock <= item.reorder_level:
            return 'warning'
        else:
            return 'success'


def register_shell_context(app):
    """Register shell context for flask shell command"""
    
    @app.shell_context_processor
    def make_shell_context():
        """Add database and models to shell context"""
        from app.models.normalized.item import Item
        from app.models.normalized.category import Category
        from app.models.normalized.supplier import Supplier
        from app.models.normalized.location import Location
        from app.models.normalized.transaction import Transaction
        from app.models.normalized.transaction_type import TransactionType
        
        return {
            'db': db,
            'Item': Item,
            'Category': Category,
            'Supplier': Supplier,
            'Location': Location,
            'Transaction': Transaction,
            'TransactionType': TransactionType
        }


# Context Processors - Make variables available to all templates

def register_context_processors(app):
    """Register context processors"""
    
    @app.context_processor
    def inject_app_info():
        """Inject application information into all templates"""
        return {
            'app_name': 'Inventory Management System',
            'app_version': '1.0.0'
        }


# Before/After Request Handlers

def register_request_handlers(app):
    """Register before/after request handlers"""
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        # You can add logic here like checking authentication, logging, etc.
        pass
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove database session after each request"""
        db.session.remove()


# CLI Commands (Optional - for development)

def register_cli_commands(app):
    """Register custom CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database with tables and seed data"""
        from app.models.normalized.transaction_type import TransactionType
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Seed transaction types
        transaction_types = [
            TransactionType(type_name='STOCK_IN', description='Stock received from supplier'),
            TransactionType(type_name='STOCK_OUT', description='Stock issued/sold'),
            TransactionType(type_name='ADJUSTMENT', description='Stock adjustment/correction'),
            TransactionType(type_name='RETURN', description='Stock returned from customer')
        ]
        
        for tt in transaction_types:
            existing = db.session.query(TransactionType).filter_by(type_name=tt.type_name).first()
            if not existing:
                db.session.add(tt)
        
        db.session.commit()
        print("✓ Transaction types seeded")
        print("Database initialization complete!")
    
    @app.cli.command()
    def seed_sample_data():
        """Seed database with sample data for testing"""
        from app.models.normalized.category import Category
        from app.models.normalized.supplier import Supplier
        from app.models.normalized.location import Location
        from app.models.normalized.item import Item
        
        # Sample Categories
        categories = [
            Category(category_name='Electronics', description='Electronic devices and components'),
            Category(category_name='Office Supplies', description='Office furniture and supplies'),
            Category(category_name='Hardware', description='Tools and hardware items'),
        ]
        
        for cat in categories:
            db.session.add(cat)
        db.session.commit()
        print("✓ Categories added")
        
        # Sample Suppliers
        suppliers = [
            Supplier(
                supplier_name='Tech Supplies Inc.',
                contact_person='John Doe',
                email='john@techsupplies.com',
                phone='+1-555-0100'
            ),
            Supplier(
                supplier_name='Office World',
                contact_person='Jane Smith',
                email='jane@officeworld.com',
                phone='+1-555-0200'
            ),
        ]
        
        for sup in suppliers:
            db.session.add(sup)
        db.session.commit()
        print("✓ Suppliers added")
        
        # Sample Locations
        locations = [
            Location(warehouse='Main', aisle='A1', shelf='S1', bin='B01'),
            Location(warehouse='Main', aisle='A2', shelf='S2', bin='B01'),
        ]
        
        for loc in locations:
            db.session.add(loc)
        db.session.commit()
        print("✓ Locations added")
        
        # Sample Items
        items = [
            Item(
                item_code='ELEC-001',
                item_name='Dell Laptop i7',
                description='High-performance laptop for business use',
                category_id=1,
                supplier_id=1,
                location_id=1,
                unit_price=999.99,
                current_stock=25,
                reorder_level=10
            ),
            Item(
                item_code='OFF-001',
                item_name='Office Chair Pro',
                description='Ergonomic office chair with lumbar support',
                category_id=2,
                supplier_id=2,
                location_id=2,
                unit_price=299.99,
                current_stock=15,
                reorder_level=5
            ),
        ]
        
        for item in items:
            db.session.add(item)
        db.session.commit()
        print("✓ Items added")
        
        print("Sample data seeding complete!")
    
    @app.cli.command()
    def reset_db():
        """Drop all tables and recreate (CAUTION: Deletes all data!)"""
        if input("Are you sure? This will delete all data (yes/no): ").lower() == 'yes':
            db.drop_all()
            db.create_all()
            print("✓ Database reset complete")
        else:
            print("Operation cancelled")


# Import models to ensure they're registered

def import_models():
    """Import all models to ensure they're registered with SQLAlchemy"""
    from app.models.normalized import (
        category, supplier, location, item, 
        transaction, transaction_type
    )
    # Import denormalized models if needed
    # from app.models.denormalized import item_denorm, transaction_denorm