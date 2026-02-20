import json

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.database import get_db

job_bp = Blueprint('job', __name__)


@job_bp.route('/analyses', methods=['GET'])
@login_required
def list_analyses():
    db = get_db()
    rows = db.execute(
        'SELECT id, job_description, extracted_keywords, focus_suggestions, '
        'alignment_data, is_active, created_at '
        'FROM job_analyses WHERE user_id = ? ORDER BY created_at DESC',
        (current_user.id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@job_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    job_description = data.get('job_description', '').strip()
    if not job_description:
        return jsonify({'error': 'Job description is required'}), 400

    try:
        from app.services.openai_service import analyze_job
        result = analyze_job(current_user.id, job_description)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

    db = get_db()
    db.execute(
        'INSERT INTO job_analyses (user_id, job_description, extracted_keywords, '
        'focus_suggestions, alignment_data, is_active) VALUES (?, ?, ?, ?, ?, 1)',
        (
            current_user.id,
            job_description,
            json.dumps(result.get('extracted_keywords', [])),
            json.dumps(result.get('focus_suggestions', [])),
            json.dumps(result.get('alignment_data', [])),
        ),
    )

    # Deactivate all others
    new_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.execute(
        'UPDATE job_analyses SET is_active = 0 WHERE user_id = ? AND id != ?',
        (current_user.id, new_id),
    )
    db.commit()

    return jsonify({'message': 'Analysis complete', 'id': new_id}), 201


@job_bp.route('/analyses/<int:analysis_id>/activate', methods=['PUT'])
@login_required
def activate_analysis(analysis_id):
    db = get_db()
    existing = db.execute(
        'SELECT id FROM job_analyses WHERE id = ? AND user_id = ?',
        (analysis_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Analysis not found'}), 404

    db.execute(
        'UPDATE job_analyses SET is_active = 0 WHERE user_id = ?',
        (current_user.id,),
    )
    db.execute(
        'UPDATE job_analyses SET is_active = 1 WHERE id = ?',
        (analysis_id,),
    )
    db.commit()
    return jsonify({'message': 'Analysis activated'})


@job_bp.route('/analyses/<int:analysis_id>', methods=['DELETE'])
@login_required
def delete_analysis(analysis_id):
    db = get_db()
    existing = db.execute(
        'SELECT id FROM job_analyses WHERE id = ? AND user_id = ?',
        (analysis_id, current_user.id),
    ).fetchone()
    if existing is None:
        return jsonify({'error': 'Analysis not found'}), 404

    db.execute('DELETE FROM job_analyses WHERE id = ?', (analysis_id,))
    db.commit()
    return jsonify({'message': 'Analysis deleted'})
