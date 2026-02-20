from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.database import get_db

blurb_bp = Blueprint('blurb', __name__)


@blurb_bp.route('', methods=['GET'])
@login_required
def list_blurbs():
    template_name = request.args.get('template_name', 'classic')
    db = get_db()
    rows = db.execute(
        'SELECT id, template_name, field_key, suggestion_text, status, user_text, '
        'created_at, updated_at FROM blurbs '
        'WHERE user_id = ? AND template_name = ? ORDER BY field_key, id',
        (current_user.id, template_name),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@blurb_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    field_key = data.get('field_key', '').strip()
    template_name = data.get('template_name', 'classic').strip()

    if not field_key:
        return jsonify({'error': 'field_key is required'}), 400

    try:
        from app.services.openai_service import generate_blurbs
        suggestions = generate_blurbs(current_user.id, field_key, template_name)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

    db = get_db()
    for text in suggestions:
        db.execute(
            'INSERT INTO blurbs (user_id, template_name, field_key, suggestion_text) '
            'VALUES (?, ?, ?, ?)',
            (current_user.id, template_name, field_key, text),
        )
    db.commit()

    return jsonify({'message': f'Generated {len(suggestions)} blurbs'}), 201


@blurb_bp.route('/<int:blurb_id>', methods=['PUT'])
@login_required
def update_blurb(blurb_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    db = get_db()
    existing = db.execute(
        'SELECT id FROM blurbs WHERE id = ? AND user_id = ?',
        (blurb_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Blurb not found'}), 404

    status = data.get('status', 'pending')
    if status not in ('pending', 'accepted', 'modified', 'rejected'):
        return jsonify({'error': 'Invalid status'}), 400

    user_text = data.get('user_text', '')

    db.execute(
        'UPDATE blurbs SET status = ?, user_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (status, user_text, blurb_id),
    )
    db.commit()
    return jsonify({'message': 'Blurb updated'})


@blurb_bp.route('/<int:blurb_id>', methods=['DELETE'])
@login_required
def delete_blurb(blurb_id):
    db = get_db()
    existing = db.execute(
        'SELECT id FROM blurbs WHERE id = ? AND user_id = ?',
        (blurb_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Blurb not found'}), 404

    db.execute('DELETE FROM blurbs WHERE id = ?', (blurb_id,))
    db.commit()
    return jsonify({'message': 'Blurb deleted'})
