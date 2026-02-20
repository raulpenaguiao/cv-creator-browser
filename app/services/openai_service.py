import json

from openai import OpenAI

from app.database import get_db
from app.services.crypto_service import decrypt_api_key


def _get_client(user_id):
    db = get_db()
    row = db.execute(
        'SELECT openai_api_key_enc FROM user_settings WHERE user_id = ?',
        (user_id,),
    ).fetchone()

    if row is None or row['openai_api_key_enc'] is None:
        raise ValueError('OpenAI API key not configured. Set it in Settings.')

    api_key = decrypt_api_key(row['openai_api_key_enc'])
    return OpenAI(api_key=api_key)


def _get_user_data(user_id):
    db = get_db()

    profile = db.execute(
        'SELECT first_name, last_name, bio FROM about_you WHERE user_id = ?',
        (user_id,),
    ).fetchone()

    experiences = db.execute(
        'SELECT category, title, organization, start_date, end_date, description, keywords '
        'FROM experiences WHERE user_id = ? ORDER BY sort_order',
        (user_id,),
    ).fetchall()

    projects = db.execute(
        'SELECT title, description, keywords FROM projects WHERE user_id = ? ORDER BY sort_order',
        (user_id,),
    ).fetchall()

    return {
        'profile': dict(profile) if profile else {},
        'experiences': [dict(e) for e in experiences],
        'projects': [dict(p) for p in projects],
    }


def analyze_job(user_id, job_description):
    client = _get_client(user_id)
    user_data = _get_user_data(user_id)

    system_prompt = (
        "You are an expert career advisor. Analyze the given job description in the context "
        "of the candidate's background. Extract key requirements, suggest focus areas, and "
        "assess alignment with their experience and projects. "
        "Return your response as a JSON object with these keys:\n"
        '- "extracted_keywords": array of strings (key skills/requirements from the job)\n'
        '- "focus_suggestions": array of strings (what the candidate should emphasize)\n'
        '- "alignment_data": array of objects with "item" (experience/project name), '
        '"score" (0-100), and "explanation" (why it aligns or not)\n'
    )

    user_prompt = (
        f"## Job Description\n{job_description}\n\n"
        f"## Candidate Background\n"
        f"Name: {user_data['profile'].get('first_name', '')} {user_data['profile'].get('last_name', '')}\n"
        f"Bio: {user_data['profile'].get('bio', '')}\n\n"
        f"## Experiences\n"
    )
    for exp in user_data['experiences']:
        user_prompt += (
            f"- {exp['title']} at {exp['organization']} ({exp['category']}): "
            f"{exp['description']} [Keywords: {exp['keywords']}]\n"
        )

    user_prompt += "\n## Projects\n"
    for proj in user_data['projects']:
        user_prompt += f"- {proj['title']}: {proj['description']} [Keywords: {proj['keywords']}]\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    result = json.loads(response.choices[0].message.content)
    return result


def generate_blurbs(user_id, field_key, template_name):
    client = _get_client(user_id)
    user_data = _get_user_data(user_id)

    db = get_db()
    settings = db.execute(
        'SELECT sentences_per_field FROM user_settings WHERE user_id = ?',
        (user_id,),
    ).fetchone()
    num_sentences = settings['sentences_per_field'] if settings else 3

    # Get active job analysis
    analysis = db.execute(
        'SELECT extracted_keywords, focus_suggestions FROM job_analyses '
        'WHERE user_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1',
        (user_id,),
    ).fetchone()

    # Get template config for field context
    from app.services.template_service import get_template_config
    config = get_template_config(template_name)
    field_config = None
    if config and 'sections' in config:
        for section in config['sections']:
            if section.get('key') == field_key:
                field_config = section
                break

    system_prompt = (
        "You are a professional CV writer. Generate polished, concise CV text. "
        "Each suggestion should be a complete, self-contained statement suitable for a CV. "
        "Return your response as a JSON object with a single key:\n"
        '- "suggestions": array of strings (each is a complete CV blurb)\n'
    )

    user_prompt = f"Generate {num_sentences} CV blurb suggestions for the field: {field_key}\n\n"

    if field_config:
        if field_config.get('prompt_context'):
            user_prompt += f"Context: {field_config['prompt_context']}\n"
        if field_config.get('max_chars'):
            user_prompt += f"Max length per blurb: {field_config['max_chars']} characters\n"

    user_prompt += (
        f"\n## Candidate\n"
        f"Name: {user_data['profile'].get('first_name', '')} {user_data['profile'].get('last_name', '')}\n"
        f"Bio: {user_data['profile'].get('bio', '')}\n\n"
        f"## Experiences\n"
    )
    for exp in user_data['experiences']:
        user_prompt += f"- {exp['title']} at {exp['organization']}: {exp['description']}\n"

    user_prompt += "\n## Projects\n"
    for proj in user_data['projects']:
        user_prompt += f"- {proj['title']}: {proj['description']}\n"

    if analysis:
        keywords = json.loads(analysis['extracted_keywords']) if analysis['extracted_keywords'] else []
        suggestions = json.loads(analysis['focus_suggestions']) if analysis['focus_suggestions'] else []
        if keywords:
            user_prompt += f"\n## Target Job Keywords\n{', '.join(keywords)}\n"
        if suggestions:
            user_prompt += f"\n## Focus Areas\n" + "\n".join(f"- {s}" for s in suggestions) + "\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    result = json.loads(response.choices[0].message.content)
    return result.get('suggestions', [])
