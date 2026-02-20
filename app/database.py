import os
import sqlite3

from flask import g, current_app


def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    db_path = app.config['DATABASE']
    if db_path == ':memory:':
        return

    if not os.path.exists(db_path):
        with app.app_context():
            db = get_db()
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as f:
                db.executescript(f.read())
            db.commit()


def init_test_db():
    """Initialize an in-memory database for testing."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    db.commit()
