import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    INSTANCE_PATH = os.path.join(basedir, 'instance')
    DATABASE = os.path.join(INSTANCE_PATH, 'cv_creator.db')
    UPLOAD_FOLDER = os.path.join(INSTANCE_PATH, 'uploads')
    GENERATED_FOLDER = os.path.join(INSTANCE_PATH, 'generated')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cvcreator.local')

    WTF_CSRF_TIME_LIMIT = None  # No expiry on CSRF tokens (tied to session)

    ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_PHOTO_MIMETYPES = {
        'image/png', 'image/jpeg', 'image/gif', 'image/webp'
    }

    LATEX_TIMEOUT = 30  # seconds


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    SESSION_COOKIE_SECURE = True


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    DATABASE = ':memory:'
    INSTANCE_PATH = os.path.join(basedir, 'instance', 'test')
    UPLOAD_FOLDER = os.path.join(INSTANCE_PATH, 'uploads')
    GENERATED_FOLDER = os.path.join(INSTANCE_PATH, 'generated')
