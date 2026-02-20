import json

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user, login_required

from app.services.data_service import export_user_data, import_user_data

data_bp = Blueprint('data', __name__)


@data_bp.route('/export', methods=['GET'])
@login_required
def export_data():
    data = export_user_data(current_user.id)
    content = json.dumps(data, indent=2, default=str)
    return Response(
        content,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=cv_data_{current_user.username}.json'},
    )


@data_bp.route('/import', methods=['POST'])
@login_required
def import_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return jsonify({'error': 'Invalid JSON file'}), 400

    try:
        import_user_data(current_user.id, data)
        return jsonify({'message': 'Data imported successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 500
