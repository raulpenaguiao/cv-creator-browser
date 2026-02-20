from flask_login import UserMixin

from app.database import get_db
from app.extensions import login_manager


class User(UserMixin):
    def __init__(self, id, username, email, password_hash, created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return User.from_row(row)

    @staticmethod
    def get_by_username(username):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        return User.from_row(row)

    @staticmethod
    def get_by_email(email):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        return User.from_row(row)


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))
