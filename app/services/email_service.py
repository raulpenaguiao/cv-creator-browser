from flask import current_app, render_template, url_for
from flask_mail import Message

from app.extensions import mail


def send_password_reset_email(user_email, reset_token):
    reset_url = url_for('main.index', _external=True) + f'?reset_token={reset_token}'

    msg = Message(
        subject='CV Creator - Password Reset',
        recipients=[user_email],
    )
    msg.html = render_template('email/reset_password.html', reset_url=reset_url)
    msg.body = (
        f'You requested a password reset for your CV Creator account.\n\n'
        f'Click the following link to reset your password:\n{reset_url}\n\n'
        f'This link expires in 1 hour.\n\n'
        f'If you did not request this, please ignore this email.'
    )

    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Failed to send reset email: {e}')
