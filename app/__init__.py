import os

from flask import Flask

from config import DevConfig


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    if config is None:
        app.config.from_object(DevConfig)
    else:
        app.config.from_object(config)

    os.makedirs(app.config['INSTANCE_PATH'], exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', os.path.join(app.config['INSTANCE_PATH'], 'uploads')), exist_ok=True)
    os.makedirs(app.config.get('GENERATED_FOLDER', os.path.join(app.config['INSTANCE_PATH'], 'generated')), exist_ok=True)

    from app.extensions import login_manager, csrf, mail, limiter
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    from app.database import init_db, close_db
    init_db(app)
    app.teardown_appcontext(close_db)

    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.profile import profile_bp
    from app.blueprints.photo import photo_bp
    from app.blueprints.experience import experience_bp
    from app.blueprints.project import project_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.job import job_bp
    from app.blueprints.blurb import blurb_bp
    from app.blueprints.generate import generate_bp
    from app.blueprints.data import data_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(photo_bp, url_prefix='/api/photos')
    app.register_blueprint(experience_bp, url_prefix='/api/experiences')
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(job_bp, url_prefix='/api/job')
    app.register_blueprint(blurb_bp, url_prefix='/api/blurbs')
    app.register_blueprint(generate_bp, url_prefix='/api/generate')
    app.register_blueprint(data_bp, url_prefix='/api/data')

    return app
