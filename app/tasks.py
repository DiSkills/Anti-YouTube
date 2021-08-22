import json
import time

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
    TESTS, MEDIA_ROOT,
)

import os

from celery import Celery

from app.files import remove_file

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

password_reset_jwt_subject = 'preset'


@celery.task(name='send_email')
def send_email(
        email_to: str,
        subject_template: str = '',
        html_template: str = '',
        environment=None,
        attach: bool = False,
        file_name: str = '',
) -> None:
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
        :param attach: Attachments
        :type attach: bool
        :param file_name: File name
        :type file_name: str
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
        if attach and file_name:
            message.attach(data=open(file_name), filename=file_name.split('/')[-1])
            remove_file(file_name)

        response = message.send(to=email_to, render=environment, smtp=smtp_options)
        logging.info(f'send email result: {response}')


@celery.task(name='export_data', bind=True)
def export_data(self, data):
    from app.auth.send_emails import send_export_data

    file_name = MEDIA_ROOT + data['username'] + '.json'
    with open(file_name, 'w') as file:
        json.dump(data, file)
    total = 10
    i = 0
    for video in range(total):
        i += 1
        self.update_state(state='PROGRESS', meta={'progress': 100 * i // total})
        time.sleep(1)
    send_export_data(data['email'], file_name)
    return {'progress': 100, 'result': data}
