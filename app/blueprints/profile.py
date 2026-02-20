from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.database import get_db

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('', methods=['GET'])
@login_required
def get_profile():
    db = get_db()
    row = db.execute(
        'SELECT first_name, last_name, email_contact, phone, address, linkedin, website, bio '
        'FROM about_you WHERE user_id = ?',
        (current_user.id,),
    ).fetchone()
    if row is None:
        return jsonify({})
    return jsonify(dict(row))


@profile_bp.route('', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    fields = ['first_name', 'last_name', 'email_contact', 'phone', 'address', 'linkedin', 'website', 'bio']
    updates = {f: data.get(f, '') for f in fields}

    db = get_db()
    db.execute(
        'UPDATE about_you SET first_name=?, last_name=?, email_contact=?, phone=?, '
        'address=?, linkedin=?, website=?, bio=?, updated_at=CURRENT_TIMESTAMP '
        'WHERE user_id=?',
        (*[updates[f] for f in fields], current_user.id),
    )
    db.commit()
    return jsonify({'message': 'Profile updated'})
