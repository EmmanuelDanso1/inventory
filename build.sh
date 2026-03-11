#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
flask --app invent_app:create_app db upgrade
flask --app invent_app:create_app shell <<EOF
from invent_app import db
from invent_app.models.normalized.transaction_type import TransactionType
for name in ['STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT']:
    if not db.session.query(TransactionType).filter_by(type_name=name).first():
        db.session.add(TransactionType(type_name=name))
db.session.commit()
print("Transaction types seeded")
EOF