import json

from app.database import get_db


def export_user_data(user_id):
    db = get_db()

    profile = db.execute(
        'SELECT first_name, last_name, email_contact, phone, address, linkedin, website, bio '
        'FROM about_you WHERE user_id = ?', (user_id,)
    ).fetchone()

    experiences = db.execute(
        'SELECT category, title, organization, start_date, end_date, description, keywords, sort_order '
        'FROM experiences WHERE user_id = ? ORDER BY sort_order', (user_id,)
    ).fetchall()

    projects = db.execute(
        'SELECT title, description, keywords, sort_order '
        'FROM projects WHERE user_id = ? ORDER BY sort_order', (user_id,)
    ).fetchall()

    job_analyses = db.execute(
        'SELECT job_description, extracted_keywords, focus_suggestions, alignment_data, is_active, created_at '
        'FROM job_analyses WHERE user_id = ? ORDER BY created_at', (user_id,)
    ).fetchall()

    blurbs = db.execute(
        'SELECT template_name, field_key, suggestion_text, status, user_text '
        'FROM blurbs WHERE user_id = ?', (user_id,)
    ).fetchall()

    settings = db.execute(
        'SELECT selected_template, sentences_per_field, font_size '
        'FROM user_settings WHERE user_id = ?', (user_id,)
    ).fetchone()

    return {
        'version': 1,
        'profile': dict(profile) if profile else {},
        'experiences': [dict(e) for e in experiences],
        'projects': [dict(p) for p in projects],
        'job_analyses': [dict(j) for j in job_analyses],
        'blurbs': [dict(b) for b in blurbs],
        'settings': dict(settings) if settings else {},
    }


def import_user_data(user_id, data):
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('Invalid data format')

    db = get_db()

    # Import profile
    if 'profile' in data:
        p = data['profile']
        db.execute(
            'UPDATE about_you SET first_name=?, last_name=?, email_contact=?, phone=?, '
            'address=?, linkedin=?, website=?, bio=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?',
            (
                p.get('first_name', ''), p.get('last_name', ''),
                p.get('email_contact', ''), p.get('phone', ''),
                p.get('address', ''), p.get('linkedin', ''),
                p.get('website', ''), p.get('bio', ''),
                user_id,
            ),
        )

    # Import experiences (clear existing first)
    if 'experiences' in data:
        db.execute('DELETE FROM experiences WHERE user_id = ?', (user_id,))
        for idx, exp in enumerate(data['experiences']):
            db.execute(
                'INSERT INTO experiences (user_id, category, title, organization, start_date, '
                'end_date, description, keywords, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    user_id, exp.get('category', 'work'), exp.get('title', ''),
                    exp.get('organization', ''), exp.get('start_date', ''),
                    exp.get('end_date', ''), exp.get('description', ''),
                    exp.get('keywords', ''), exp.get('sort_order', idx),
                ),
            )

    # Import projects
    if 'projects' in data:
        db.execute('DELETE FROM projects WHERE user_id = ?', (user_id,))
        for idx, proj in enumerate(data['projects']):
            db.execute(
                'INSERT INTO projects (user_id, title, description, keywords, sort_order) '
                'VALUES (?, ?, ?, ?, ?)',
                (
                    user_id, proj.get('title', ''), proj.get('description', ''),
                    proj.get('keywords', ''), proj.get('sort_order', idx),
                ),
            )

    # Import job analyses
    if 'job_analyses' in data:
        db.execute('DELETE FROM job_analyses WHERE user_id = ?', (user_id,))
        for j in data['job_analyses']:
            keywords = j.get('extracted_keywords', '[]')
            if isinstance(keywords, list):
                keywords = json.dumps(keywords)
            focus = j.get('focus_suggestions', '[]')
            if isinstance(focus, list):
                focus = json.dumps(focus)
            alignment = j.get('alignment_data', '[]')
            if isinstance(alignment, list):
                alignment = json.dumps(alignment)

            db.execute(
                'INSERT INTO job_analyses (user_id, job_description, extracted_keywords, '
                'focus_suggestions, alignment_data, is_active) VALUES (?, ?, ?, ?, ?, ?)',
                (
                    user_id, j.get('job_description', ''),
                    keywords, focus, alignment,
                    j.get('is_active', 0),
                ),
            )

    # Import blurbs
    if 'blurbs' in data:
        db.execute('DELETE FROM blurbs WHERE user_id = ?', (user_id,))
        for b in data['blurbs']:
            db.execute(
                'INSERT INTO blurbs (user_id, template_name, field_key, suggestion_text, status, user_text) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (
                    user_id, b.get('template_name', 'classic'),
                    b.get('field_key', ''), b.get('suggestion_text', ''),
                    b.get('status', 'pending'), b.get('user_text', ''),
                ),
            )

    # Import settings (except API key)
    if 'settings' in data:
        s = data['settings']
        if 'selected_template' in s:
            db.execute(
                'UPDATE user_settings SET selected_template=? WHERE user_id=?',
                (s['selected_template'], user_id),
            )
        if 'sentences_per_field' in s:
            db.execute(
                'UPDATE user_settings SET sentences_per_field=? WHERE user_id=?',
                (s['sentences_per_field'], user_id),
            )
        if 'font_size' in s:
            db.execute(
                'UPDATE user_settings SET font_size=? WHERE user_id=?',
                (s['font_size'], user_id),
            )

    db.commit()
