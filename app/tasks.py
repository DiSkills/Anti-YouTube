import emails
from emails.template import JinjaTemplate

import logging

from app.config import (
    EMAILS_ENABLED,
    EMAILS_FROM_EMAIL,
    EMAILS_FROM_NAME,
    SMTP_TLS,
    SMTP_USER,
    SMTP_PORT,
    SMTP_HOST,
    SMTP_PASSWORD,
    TESTS,
)

import os

from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

password_reset_jwt_subject = 'preset'


@celery.task(name='send_email')
def send_email(email_to: str, subject_template: str = '', html_template: str = '', environment=None) -> None:
    """
        Send email
        :param email_to: Email to user
        :type email_to: str
        :param subject_template: Subject template
        :type subject_template: str
        :param html_template: Html body template
        :type html_template: str
        :param environment: Environment
        :type environment: dict
        :return: None
    """
    if environment is None:
        environment = {}

    assert EMAILS_ENABLED, 'no provided configuration for email variables'
    message = emails.Message(
        subject=JinjaTemplate(subject_template),
        html=JinjaTemplate(html_template),
        mail_from=(EMAILS_FROM_NAME, EMAILS_FROM_EMAIL),
    )
    smtp_options = {'host': SMTP_HOST, 'port': SMTP_PORT}
    if SMTP_TLS:
        smtp_options['tls'] = True
    if SMTP_USER:
        smtp_options['user'] = SMTP_USER
    if SMTP_PASSWORD:
        smtp_options['password'] = SMTP_PASSWORD
    if not TESTS:
        response = message.send(to=email_to, render=environment, smtp=smtp_options)
        logging.info(f'send email result: {response}')

