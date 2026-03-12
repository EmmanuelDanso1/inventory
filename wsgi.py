import os
from invent_app import create_app, db

app = create_app()

with app.app_context():
    # Seed transaction types
    from invent_app.models.normalized.transaction_type import TransactionType
    for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
        db.session.add(TransactionType(type_name=name))
    db.session.commit()
    print("Database initialized")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)