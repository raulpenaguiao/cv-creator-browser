import os

from flask import Blueprint, current_app, jsonify, send_file
from flask_login import current_user, login_required

from app.database import get_db

generate_bp = Blueprint('generate', __name__)


@generate_bp.route('/compile', methods=['POST'])
@login_required
def compile_cv():
    db = get_db()
    settings = db.execute(
        'SELECT selected_template FROM user_settings WHERE user_id = ?',
        (current_user.id,),
    ).fetchone()
    template_name = settings['selected_template'] if settings else 'classic'

    try:
        from app.services.latex_service import compile_pdf
        pdf_path, tex_path = compile_pdf(current_user.id, template_name)
        return jsonify({'message': 'CV compiled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@generate_bp.route('/download/pdf', methods=['GET'])
@login_required
def download_pdf():
    gen_dir = os.path.join(current_app.config['GENERATED_FOLDER'], str(current_user.id))
    pdf_path = os.path.join(gen_dir, 'cv.pdf')
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'No compiled CV found. Compile first.'}), 404
    return send_file(pdf_path, mimetype='application/pdf', as_attachment=True, download_name='cv.pdf')


@generate_bp.route('/download/tex', methods=['GET'])
@login_required
def download_tex():
    gen_dir = os.path.join(current_app.config['GENERATED_FOLDER'], str(current_user.id))
    tex_path = os.path.join(gen_dir, 'cv.tex')
    if not os.path.exists(tex_path):
        return jsonify({'error': 'No compiled CV found. Compile first.'}), 404
    return send_file(tex_path, mimetype='application/x-tex', as_attachment=True, download_name='cv.tex')
