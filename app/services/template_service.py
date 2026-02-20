import json
import os

from flask import current_app


def _templates_dir():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cv_templates')


def get_available_templates():
    templates = []
    tdir = _templates_dir()
    if not os.path.isdir(tdir):
        return templates

    for name in sorted(os.listdir(tdir)):
        config_path = os.path.join(tdir, name, 'config.json')
        if os.path.isfile(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            config['name'] = name
            templates.append(config)
    return templates


def get_template_config(template_name):
    config_path = os.path.join(_templates_dir(), template_name, 'config.json')
    if not os.path.isfile(config_path):
        return None
    with open(config_path, 'r') as f:
        config = json.load(f)
    config['name'] = template_name
    return config


def get_template_tex_path(template_name):
    tex_path = os.path.join(_templates_dir(), template_name, 'template.tex')
    if not os.path.isfile(tex_path):
        return None
    return tex_path
