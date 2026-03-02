from invent_app import create_app
import os

app = create_app()

if __name__ == '__main__':
    app.run(
        host='127.0.0l1',
        port=5000,
        debug=True
    )