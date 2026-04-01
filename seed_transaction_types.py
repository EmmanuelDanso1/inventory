import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

from invent_app import create_app, db
from invent_app.models.normalized.transaction_type import TransactionType

app = create_app()
with app.app_context():
    for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
        existing = db.session.query(TransactionType).filter_by(type_name=name).first()
        if not existing:
            db.session.add(TransactionType(type_name=name))
    try:
        db.session.commit()
        print("Transaction types seeded successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Skipped: {e}")