import emails
from emails.template import JinjaTemplate

import logging

from config import (
    EMAILS_ENABLED,
    EMAILS_FROM_EMAIL,
    EMAILS_FROM_NAME,
    SMTP_TLS,
    SMTP_USER,
    SMTP_PORT,
    SMTP_HOST,
    SMTP_PASSWORD,
)

password_reset_jwt_subject = 'preset'


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
    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logging.info(f'send email result: {response}')
