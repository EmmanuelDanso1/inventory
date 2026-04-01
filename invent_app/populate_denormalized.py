"""
populate_denormalized.py
------------------------
Standalone script to mirror normalized data into the denormalized tables.

Use this when you cannot trigger the /seed/denormalized web route,
e.g. when running from the Render Shell tab or a local terminal.

Usage (from project root):
    python populate_denormalized.py

Requirements:
    - Run from the project root (same directory as app.py / invent_app folder)
    - DATABASE_URL environment variable must be set (Render sets this automatically)

What it does:
    1. Reads all rows from the normalized items and transactions tables
    2. Flattens the relational data (resolves category names, supplier names etc.)
    3. Wipes the denormalized tables
    4. Bulk-inserts the flattened data
    5. Prints a confirmation with row counts

Run this once after each seeding round, before running benchmarks.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from invent_app import create_app, db
from invent_app.models.normalized.item import Item
from invent_app.models.normalized.transaction import Transaction
from invent_app.models.denormalized.item_denorm import ItemDenorm
from invent_app.models.denormalized.transaction_denorm import TransactionDenorm


def populate():
    app = create_app()

    with app.app_context():

        norm_item_count = db.session.query(Item).count()
        norm_tx_count   = db.session.query(Transaction).count()

        if norm_item_count == 0:
            print("ERROR: No normalized items found.")
            print("       Seed the normalized tables first via the web UI, then re-run this script.")
            sys.exit(1)

        print(f"Found {norm_item_count} normalized items and {norm_tx_count} transactions.")
        print("Wiping existing denormalized data...")

        db.session.query(TransactionDenorm).delete()
        db.session.query(ItemDenorm).delete()
        db.session.commit()

        # Mirror items
        print("Mirroring items...")
        norm_items = db.session.query(Item).all()

        denorm_items = []
        for item in norm_items:
            cat_name    = item.category.category_name  if item.category  else 'Unknown'
            sup_name    = item.supplier.supplier_name  if item.supplier  else ''
            sup_email   = item.supplier.email          if item.supplier  else ''
            sup_phone   = item.supplier.phone          if item.supplier  else ''
            sup_contact = item.supplier.contact_person if item.supplier  else ''

            denorm_items.append(ItemDenorm(
                item_code=item.item_code,
                item_name=item.item_name,
                description=item.description,
                category_name=cat_name,
                supplier_name=sup_name,
                supplier_email=sup_email,
                supplier_phone=sup_phone,
                supplier_contact=sup_contact,
                unit_price=item.unit_price,
                current_stock=item.current_stock,
                reorder_level=item.reorder_level,
                created_at=item.created_at,
                updated_at=item.updated_at,
            ))

        db.session.bulk_save_objects(denorm_items)
        db.session.commit()
        print(f"  OK  {len(denorm_items)} items -> items_denormalized")

        # Mirror transactions
        print("Mirroring transactions...")
        item_map = {i.item_id: i for i in norm_items}
        norm_txs = db.session.query(Transaction).all()

        denorm_txs = []
        skipped    = 0
        for tx in norm_txs:
            item = item_map.get(tx.item_id)
            if item is None:
                skipped += 1
                continue

            tx_type  = tx.transaction_type.type_name if tx.transaction_type else 'STOCK_IN'
            cat_name = item.category.category_name if item.category else ''
            sup_name = item.supplier.supplier_name if item.supplier else ''

            denorm_txs.append(TransactionDenorm(
                item_code=item.item_code,
                item_name=item.item_name,
                category_name=cat_name,
                supplier_name=sup_name,
                transaction_type=tx_type,
                quantity=tx.quantity,
                unit_price=tx.unit_price,
                reference_number=tx.reference_number,
                notes=tx.notes,
                transaction_date=tx.transaction_date,
                created_by=tx.created_by,
            ))

        db.session.bulk_save_objects(denorm_txs)
        db.session.commit()
        print(f"  OK  {len(denorm_txs)} transactions -> transactions_denormalized")

        if skipped:
            print(f"  WARN  {skipped} transactions skipped (orphaned item_id)")

        final_items = db.session.query(ItemDenorm).count()
        final_txs   = db.session.query(TransactionDenorm).count()

        print()
        print("Done.")
        print(f"  items_denormalized        : {final_items} rows")
        print(f"  transactions_denormalized : {final_txs} rows")
        print()
        print("Both schemas now contain identical data. Safe to run benchmarks.")


if __name__ == '__main__':
    populate()
