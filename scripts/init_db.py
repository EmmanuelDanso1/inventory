from invent_app import create_app, db
from invent_app.models.normalized.transaction_type import TransactionType

app = create_app()

with app.app_context():
    db.create_all()

    types = ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']

    for name in types:
        existing = TransactionType.query.filter_by(type_name=name).first()
        if not existing:
            db.session.add(TransactionType(type_name=name))

    db.session.commit()
    print("Database initialized safely")