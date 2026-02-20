import os

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.database import get_db
from app.services.crypto_service import encrypt_api_key

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('', methods=['GET'])
@login_required
def get_settings():
    db = get_db()
    row = db.execute(
        'SELECT openai_api_key_enc, selected_template, sentences_per_field, font_size '
        'FROM user_settings WHERE user_id = ?',
        (current_user.id,),
    ).fetchone()
    if row is None:
        return jsonify({})

    return jsonify({
        'openai_api_key_set': row['openai_api_key_enc'] is not None and len(row['openai_api_key_enc']) > 0,
        'selected_template': row['selected_template'],
        'sentences_per_field': row['sentences_per_field'],
        'font_size': row['font_size'],
    })


@settings_bp.route('', methods=['PUT'])
@login_required
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    db = get_db()

    # Handle API key separately (encrypted)
    api_key = data.get('openai_api_key', '').strip()
    if api_key:
        encrypted = encrypt_api_key(api_key)
        db.execute(
            'UPDATE user_settings SET openai_api_key_enc = ? WHERE user_id = ?',
            (encrypted, current_user.id),
        )

    # Update other settings
    if 'selected_template' in data:
        db.execute(
            'UPDATE user_settings SET selected_template = ? WHERE user_id = ?',
            (data['selected_template'], current_user.id),
        )
    if 'sentences_per_field' in data:
        val = max(1, min(10, int(data['sentences_per_field'])))
        db.execute(
            'UPDATE user_settings SET sentences_per_field = ? WHERE user_id = ?',
            (val, current_user.id),
        )
    if 'font_size' in data:
        val = max(8, min(14, int(data['font_size'])))
        db.execute(
            'UPDATE user_settings SET font_size = ? WHERE user_id = ?',
            (val, current_user.id),
        )

    db.execute(
        'UPDATE user_settings SET updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
        (current_user.id,),
    )
    db.commit()
    return jsonify({'message': 'Settings updated'})


@settings_bp.route('/templates', methods=['GET'])
@login_required
def list_templates():
    from app.services.template_service import get_available_templates
    templates = get_available_templates()
    return jsonify({'templates': templates})
