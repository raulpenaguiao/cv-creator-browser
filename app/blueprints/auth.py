from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user

from app.extensions import limiter
from app.models import User
from app.services.auth_service import (
    authenticate_user,
    create_reset_token,
    register_user,
    validate_reset_token,
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/session', methods=['GET'])
def session():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
            },
        })
    return jsonify({'authenticated': False})


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()

    if not username or not email:
        return jsonify({'error': 'Username and email are required'}), 400

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400

    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    existing = User.get_by_username(username)
    if existing:
        return jsonify({'error': 'Username already taken'}), 409

    existing = User.get_by_email(email)
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    try:
        password, user_id = register_user(username, email)
    except Exception:
        return jsonify({'error': 'Registration failed'}), 500

    return jsonify({
        'message': 'Registration successful',
        'password': password,
        'username': username,
    }), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = authenticate_user(username, password)
    if user is None:
        return jsonify({'error': 'Invalid username or password'}), 401

    login_user(user)
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})


@auth_bp.route('/reset-request', methods=['POST'])
@limiter.limit("3 per minute")
def reset_request():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # Always return success to prevent email enumeration
    user = User.get_by_email(email)
    if user:
        token = create_reset_token(user.id)
        try:
            from app.services.email_service import send_password_reset_email
            send_password_reset_email(email, token)
        except Exception:
            from flask import current_app
            current_app.logger.warning(f'Failed to send reset email, token: {token}')

    return jsonify({'message': 'If that email is registered, a reset link has been sent.'})


@auth_bp.route('/reset-confirm', methods=['POST'])
def reset_confirm():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    token = data.get('token', '')
    if not token:
        return jsonify({'error': 'Token is required'}), 400

    new_password = validate_reset_token(token)
    if new_password is None:
        return jsonify({'error': 'Invalid or expired token'}), 400

    return jsonify({
        'message': 'Password has been reset',
        'password': new_password,
    })
