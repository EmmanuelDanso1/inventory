import os
os.environ.setdefault('DATABASE_URL', os.getenv('DATABASE_URL', ''))

from invent_app import create_app, db
from invent_app.models.normalized.transaction_type import TransactionType

app = create_app()
with app.app_context():
    for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
        if not db.session.query(TransactionType).filter_by(type_name=name).first():
            db.session.add(TransactionType(type_name=name))
    db.session.commit()
    print("Transaction types seeded")