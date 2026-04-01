import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False') == 'True'
    
    # Pagination
    ITEMS_PER_PAGE = 20
    

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

# Render configuration for deployment
# import os
# from dotenv import load_dotenv

# basedir = os.path.abspath(os.path.dirname(__file__))
# load_dotenv(os.path.join(basedir, '.env'), override=False)

# class Config:
#     # Flask
#     SECRET_KEY = os.environ.get('SECRET_KEY')

#     # Fix Render's postgres:// → postgresql://
#     _db_url = os.environ.get('DATABASE_URL', '')
#     if _db_url.startswith('postgres://'):
#         _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
#     SQLALCHEMY_DATABASE_URI = _db_url

#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False') == 'True'

#     # Pagination
#     ITEMS_PER_PAGE = 20


# class ProductionConfig(Config):
#     DEBUG = False
#     SQLALCHEMY_ECHO = False