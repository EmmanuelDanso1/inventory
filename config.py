import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:password@localhost:5432/inventory_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False') == 'True'
    
    # Database Pool
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
    #     'pool_recycle': 3600,
    #     'pool_pre_ping': True,
    #     'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20))
    # }
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Performance Testing
    # PERF_TEST_DATA_SIZE = int(os.environ.get('PERF_TEST_DATA_SIZE', 10000))

# class DevelopmentConfig(Config):
#     DEBUG = True
#     SQLALCHEMY_ECHO = True

# class ProductionConfig(Config):
#     DEBUG = False
#     SQLALCHEMY_ECHO = False

# class TestingConfig(Config):
#     TESTING = True
#     SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost:5432/inventory_test'
#     WTF_CSRF_ENABLED = False

# config = {
#     'development': DevelopmentConfig,
#     'production': ProductionConfig,
#     'testing': TestingConfig,
#     'default': DevelopmentConfig
# }