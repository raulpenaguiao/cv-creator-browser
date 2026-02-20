from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.database import get_db

experience_bp = Blueprint('experience', __name__)

VALID_CATEGORIES = {'work', 'education', 'hobby'}


@experience_bp.route('', methods=['GET'])
@login_required
def list_experiences():
    db = get_db()
    rows = db.execute(
        'SELECT id, category, title, organization, start_date, end_date, '
        'description, keywords, sort_order, created_at, updated_at '
        'FROM experiences WHERE user_id = ? ORDER BY sort_order, id',
        (current_user.id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@experience_bp.route('', methods=['POST'])
@login_required
def create_experience():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    title = data.get('title', '').strip()
    category = data.get('category', '').strip()

    if not title:
        return jsonify({'error': 'Title is required'}), 400
    if category not in VALID_CATEGORIES:
        return jsonify({'error': f'Category must be one of: {", ".join(VALID_CATEGORIES)}'}), 400

    db = get_db()
    row = db.execute(
        'SELECT COALESCE(MAX(sort_order), -1) + 1 as next_order FROM experiences WHERE user_id = ?',
        (current_user.id,),
    ).fetchone()

    db.execute(
        'INSERT INTO experiences (user_id, category, title, organization, start_date, end_date, '
        'description, keywords, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            current_user.id, category, title,
            data.get('organization', ''), data.get('start_date', ''),
            data.get('end_date', ''), data.get('description', ''),
            data.get('keywords', ''), row['next_order'],
        ),
    )
    db.commit()
    return jsonify({'message': 'Experience created'}), 201


@experience_bp.route('/<int:exp_id>', methods=['PUT'])
@login_required
def update_experience(exp_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    db = get_db()
    existing = db.execute(
        'SELECT id FROM experiences WHERE id = ? AND user_id = ?',
        (exp_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Experience not found'}), 404

    title = data.get('title', '').strip()
    category = data.get('category', '').strip()

    if not title:
        return jsonify({'error': 'Title is required'}), 400
    if category not in VALID_CATEGORIES:
        return jsonify({'error': f'Category must be one of: {", ".join(VALID_CATEGORIES)}'}), 400

    db.execute(
        'UPDATE experiences SET category=?, title=?, organization=?, start_date=?, end_date=?, '
        'description=?, keywords=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
        (
            category, title, data.get('organization', ''),
            data.get('start_date', ''), data.get('end_date', ''),
            data.get('description', ''), data.get('keywords', ''),
            exp_id,
        ),
    )
    db.commit()
    return jsonify({'message': 'Experience updated'})


@experience_bp.route('/<int:exp_id>', methods=['DELETE'])
@login_required
def delete_experience(exp_id):
    db = get_db()
    existing = db.execute(
        'SELECT id FROM experiences WHERE id = ? AND user_id = ?',
        (exp_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Experience not found'}), 404

    db.execute('DELETE FROM experiences WHERE id = ?', (exp_id,))
    db.commit()
    return jsonify({'message': 'Experience deleted'})


@experience_bp.route('/reorder', methods=['PUT'])
@login_required
def reorder_experiences():
    data = request.get_json()
    if not data or 'order' not in data:
        return jsonify({'error': 'Order list required'}), 400

    db = get_db()
    for idx, exp_id in enumerate(data['order']):
        db.execute(
            'UPDATE experiences SET sort_order = ? WHERE id = ? AND user_id = ?',
            (idx, exp_id, current_user.id),
        )
    db.commit()
    return jsonify({'message': 'Reordered'})
