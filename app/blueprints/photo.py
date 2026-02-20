import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.database import get_db

photo_bp = Blueprint('photo', __name__)


def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_PHOTO_EXTENSIONS']


@photo_bp.route('', methods=['GET'])
@login_required
def list_photos():
    db = get_db()
    rows = db.execute(
        'SELECT id, filename, mime_type, is_primary, sort_order, created_at '
        'FROM photos WHERE user_id = ? ORDER BY sort_order, id',
        (current_user.id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@photo_bp.route('', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo file provided'}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Check MIME type
    try:
        import magic
        file_bytes = file.read()
        mime = magic.from_buffer(file_bytes, mime=True)
        file.seek(0)
        if mime not in current_app.config['ALLOWED_PHOTO_MIMETYPES']:
            return jsonify({'error': 'Invalid file type'}), 400
    except ImportError:
        # python-magic not installed, skip MIME check
        file_bytes = None
        mime = file.content_type or 'image/jpeg'

    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, unique_name)

    if file_bytes:
        with open(filepath, 'wb') as f:
            f.write(file_bytes)
    else:
        file.save(filepath)

    db = get_db()
    # Get max sort_order
    row = db.execute(
        'SELECT COALESCE(MAX(sort_order), -1) + 1 as next_order FROM photos WHERE user_id = ?',
        (current_user.id,),
    ).fetchone()

    db.execute(
        'INSERT INTO photos (user_id, filename, storage_path, mime_type, sort_order) VALUES (?, ?, ?, ?, ?)',
        (current_user.id, safe_name, filepath, mime, row['next_order']),
    )
    db.commit()

    return jsonify({'message': 'Photo uploaded'}), 201


@photo_bp.route('/<int:photo_id>', methods=['DELETE'])
@login_required
def delete_photo(photo_id):
    db = get_db()
    row = db.execute(
        'SELECT * FROM photos WHERE id = ? AND user_id = ?',
        (photo_id, current_user.id),
    ).fetchone()
    if row is None:
        return jsonify({'error': 'Photo not found'}), 404

    # Delete file
    try:
        os.remove(row['storage_path'])
    except OSError:
        pass

    db.execute('DELETE FROM photos WHERE id = ?', (photo_id,))
    db.commit()
    return jsonify({'message': 'Photo deleted'})


@photo_bp.route('/<int:photo_id>/primary', methods=['PUT'])
@login_required
def set_primary(photo_id):
    db = get_db()
    row = db.execute(
        'SELECT id FROM photos WHERE id = ? AND user_id = ?',
        (photo_id, current_user.id),
    ).fetchone()
    if row is None:
        return jsonify({'error': 'Photo not found'}), 404

    db.execute('UPDATE photos SET is_primary = 0 WHERE user_id = ?', (current_user.id,))
    db.execute('UPDATE photos SET is_primary = 1 WHERE id = ?', (photo_id,))
    db.commit()
    return jsonify({'message': 'Primary photo set'})


@photo_bp.route('/<int:photo_id>/file', methods=['GET'])
@login_required
def get_file(photo_id):
    db = get_db()
    row = db.execute(
        'SELECT storage_path, mime_type FROM photos WHERE id = ? AND user_id = ?',
        (photo_id, current_user.id),
    ).fetchone()
    if row is None:
        return jsonify({'error': 'Photo not found'}), 404

    return send_file(row['storage_path'], mimetype=row['mime_type'])
