from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .app import create_app