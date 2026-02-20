import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt

from app.database import get_db
from app.models import User


def generate_password(length=16):
    return secrets.token_urlsafe(length)


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def register_user(username, email):
    db = get_db()
    password = generate_password()
    pw_hash = hash_password(password)

    db.execute(
        'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
        (username, email, pw_hash),
    )
    user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    db.execute(
        'INSERT INTO user_settings (user_id) VALUES (?)',
        (user_id,),
    )
    db.execute(
        'INSERT INTO about_you (user_id) VALUES (?)',
        (user_id,),
    )
    db.commit()

    return password, user_id


def authenticate_user(username, password):
    user = User.get_by_username(username)
    if user is None:
        return None
    if not check_password(password, user.password_hash):
        return None
    return user


def create_reset_token(user_id):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    db = get_db()
    db.execute(
        'INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)',
        (user_id, token_hash, expires_at.isoformat()),
    )
    db.commit()
    return token


def validate_reset_token(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db = get_db()
    row = db.execute(
        'SELECT * FROM password_reset_tokens WHERE token_hash = ? AND used = 0',
        (token_hash,),
    ).fetchone()

    if row is None:
        return None

    expires_at = datetime.fromisoformat(row['expires_at'])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        return None

    # Mark as used
    db.execute(
        'UPDATE password_reset_tokens SET used = 1 WHERE id = ?',
        (row['id'],),
    )

    # Generate new password
    new_password = generate_password()
    pw_hash = hash_password(new_password)
    db.execute(
        'UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (pw_hash, row['user_id']),
    )
    db.commit()

    return new_password
