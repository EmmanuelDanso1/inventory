import os
from invent_app import create_app, db
from flask_migrate import upgrade

app = create_app()

with app.app_context():
    upgrade()  # runs flask db upgrade on every startup

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)