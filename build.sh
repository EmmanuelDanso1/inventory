#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
flask --app invent_app:create_app db upgrade
python seed_transaction_types.py