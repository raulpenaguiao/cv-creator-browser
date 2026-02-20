import json
import os
import shutil
import subprocess
import tempfile

from jinja2 import BaseLoader, Environment

from app.database import get_db
from app.services.template_service import get_template_config, get_template_tex_path


# LaTeX special characters that must be escaped
LATEX_SPECIAL = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
    '\\': r'\textbackslash{}',
}


def sanitize_latex(text):
    if not text:
        return ''
    result = str(text)
    # Must escape backslash first to avoid double-escaping
    result = result.replace('\\', '\x00BACKSLASH\x00')
    for char, replacement in LATEX_SPECIAL.items():
        if char == '\\':
            continue
        result = result.replace(char, replacement)
    result = result.replace('\x00BACKSLASH\x00', r'\textbackslash{}')
    return result


def _build_template_context(user_id, template_name):
    db = get_db()
    config = get_template_config(template_name)
    if config is None:
        raise ValueError(f'Template "{template_name}" not found')

    # Profile data
    profile = db.execute(
        'SELECT * FROM about_you WHERE user_id = ?', (user_id,)
    ).fetchone()
    profile_dict = dict(profile) if profile else {}

    # Settings
    settings = db.execute(
        'SELECT font_size FROM user_settings WHERE user_id = ?', (user_id,)
    ).fetchone()
    font_size = settings['font_size'] if settings else 11

    # Photo
    photo = db.execute(
        'SELECT storage_path FROM photos WHERE user_id = ? AND is_primary = 1 LIMIT 1',
        (user_id,),
    ).fetchone()

    # Experiences by category
    experiences = db.execute(
        'SELECT * FROM experiences WHERE user_id = ? ORDER BY sort_order, id',
        (user_id,),
    ).fetchall()
    work = [dict(e) for e in experiences if e['category'] == 'work']
    education = [dict(e) for e in experiences if e['category'] == 'education']
    hobbies = [dict(e) for e in experiences if e['category'] == 'hobby']

    # Projects
    projects = db.execute(
        'SELECT * FROM projects WHERE user_id = ? ORDER BY sort_order, id',
        (user_id,),
    ).fetchall()
    projects_list = [dict(p) for p in projects]

    # Blurbs (accepted and modified only)
    blurbs = db.execute(
        'SELECT field_key, suggestion_text, status, user_text FROM blurbs '
        'WHERE user_id = ? AND template_name = ? AND status IN (?, ?)',
        (user_id, template_name, 'accepted', 'modified'),
    ).fetchall()

    blurb_map = {}
    for b in blurbs:
        key = b['field_key']
        text = b['user_text'] if b['status'] == 'modified' and b['user_text'] else b['suggestion_text']
        blurb_map.setdefault(key, []).append(text)

    # Sanitize all text fields
    safe_profile = {k: sanitize_latex(v) for k, v in profile_dict.items()
                    if k not in ('id', 'user_id', 'created_at', 'updated_at')}

    safe_work = []
    for w in work:
        safe_work.append({k: sanitize_latex(v) for k, v in w.items()
                          if k not in ('id', 'user_id', 'created_at', 'updated_at', 'sort_order')})

    safe_education = []
    for e in education:
        safe_education.append({k: sanitize_latex(v) for k, v in e.items()
                               if k not in ('id', 'user_id', 'created_at', 'updated_at', 'sort_order')})

    safe_hobbies = []
    for h in hobbies:
        safe_hobbies.append({k: sanitize_latex(v) for k, v in h.items()
                             if k not in ('id', 'user_id', 'created_at', 'updated_at', 'sort_order')})

    safe_projects = []
    for p in projects_list:
        safe_projects.append({k: sanitize_latex(v) for k, v in p.items()
                              if k not in ('id', 'user_id', 'created_at', 'updated_at', 'sort_order')})

    safe_blurbs = {}
    for key, texts in blurb_map.items():
        safe_blurbs[key] = [sanitize_latex(t) for t in texts]

    return {
        'profile': safe_profile,
        'font_size': font_size,
        'photo_path': photo['storage_path'] if photo else None,
        'work': safe_work,
        'education': safe_education,
        'hobbies': safe_hobbies,
        'projects': safe_projects,
        'blurbs': safe_blurbs,
        'config': config,
    }


def render_tex(user_id, template_name):
    context = _build_template_context(user_id, template_name)
    tex_path = get_template_tex_path(template_name)
    if tex_path is None:
        raise ValueError(f'Template tex file not found for "{template_name}"')

    with open(tex_path, 'r') as f:
        template_source = f.read()

    # Custom Jinja2 environment with LaTeX-friendly delimiters
    env = Environment(
        loader=BaseLoader(),
        block_start_string=r'\BLOCK{',
        block_end_string='}',
        variable_start_string=r'\VAR{',
        variable_end_string='}',
        comment_start_string=r'\#{',
        comment_end_string='}',
        autoescape=False,
    )

    template = env.from_string(template_source)
    return template.render(**context)


def compile_pdf(user_id, template_name, timeout=30):
    from flask import current_app

    tex_content = render_tex(user_id, template_name)
    timeout = current_app.config.get('LATEX_TIMEOUT', timeout)

    # Create temp directory for compilation
    tmpdir = tempfile.mkdtemp(prefix='cv_')
    tex_file = os.path.join(tmpdir, 'cv.tex')

    with open(tex_file, 'w') as f:
        f.write(tex_content)

    # Copy photo if present
    context = _build_template_context(user_id, template_name)
    if context['photo_path'] and os.path.exists(context['photo_path']):
        photo_dest = os.path.join(tmpdir, 'photo' + os.path.splitext(context['photo_path'])[1])
        shutil.copy2(context['photo_path'], photo_dest)

    try:
        # Run pdflatex twice for references
        for _ in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '--no-shell-escape', 'cv.tex'],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        pdf_path = os.path.join(tmpdir, 'cv.pdf')
        if not os.path.exists(pdf_path):
            raise RuntimeError(f'PDF compilation failed:\n{result.stdout}\n{result.stderr}')

        # Copy outputs to generated folder
        gen_dir = os.path.join(current_app.config['GENERATED_FOLDER'], str(user_id))
        os.makedirs(gen_dir, exist_ok=True)

        final_pdf = os.path.join(gen_dir, 'cv.pdf')
        final_tex = os.path.join(gen_dir, 'cv.tex')
        shutil.copy2(pdf_path, final_pdf)
        shutil.copy2(tex_file, final_tex)

        return final_pdf, final_tex
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
