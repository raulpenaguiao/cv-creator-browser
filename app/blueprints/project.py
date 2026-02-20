from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.database import get_db

project_bp = Blueprint('project', __name__)


@project_bp.route('', methods=['GET'])
@login_required
def list_projects():
    db = get_db()
    rows = db.execute(
        'SELECT id, title, description, keywords, sort_order, created_at, updated_at '
        'FROM projects WHERE user_id = ? ORDER BY sort_order, id',
        (current_user.id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@project_bp.route('', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    db = get_db()
    row = db.execute(
        'SELECT COALESCE(MAX(sort_order), -1) + 1 as next_order FROM projects WHERE user_id = ?',
        (current_user.id,),
    ).fetchone()

    db.execute(
        'INSERT INTO projects (user_id, title, description, keywords, sort_order) VALUES (?, ?, ?, ?, ?)',
        (current_user.id, title, data.get('description', ''), data.get('keywords', ''), row['next_order']),
    )
    db.commit()
    return jsonify({'message': 'Project created'}), 201


@project_bp.route('/<int:proj_id>', methods=['PUT'])
@login_required
def update_project(proj_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    db = get_db()
    existing = db.execute(
        'SELECT id FROM projects WHERE id = ? AND user_id = ?',
        (proj_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Project not found'}), 404

    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    db.execute(
        'UPDATE projects SET title=?, description=?, keywords=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
        (title, data.get('description', ''), data.get('keywords', ''), proj_id),
    )
    db.commit()
    return jsonify({'message': 'Project updated'})


@project_bp.route('/<int:proj_id>', methods=['DELETE'])
@login_required
def delete_project(proj_id):
    db = get_db()
    existing = db.execute(
        'SELECT id FROM projects WHERE id = ? AND user_id = ?',
        (proj_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Project not found'}), 404

    db.execute('DELETE FROM projects WHERE id = ?', (proj_id,))
    db.commit()
    return jsonify({'message': 'Project deleted'})


@project_bp.route('/reorder', methods=['PUT'])
@login_required
def reorder_projects():
    data = request.get_json()
    if not data or 'order' not in data:
        return jsonify({'error': 'Order list required'}), 400

    db = get_db()
    for idx, proj_id in enumerate(data['order']):
        db.execute(
            'UPDATE projects SET sort_order = ? WHERE id = ? AND user_id = ?',
            (idx, proj_id, current_user.id),
        )
    db.commit()
    return jsonify({'message': 'Reordered'})
