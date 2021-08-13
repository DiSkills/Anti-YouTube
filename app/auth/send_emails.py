from pathlib import Path
from uuid import UUID

from app.config import SERVER_HOST_FRONT_END, PROJECT_NAME, EMAIL_TEMPLATES_DIR
from app.send_emails import send_email


def send_new_account_email(email_to: str, username: str, password: str, uuid: UUID) -> None:
    """
        Activation user email send
        :param email_to: Email to user
        :type email_to: str
        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        :param uuid: Uuid
        :type uuid: UUID
        :return: None
        :rtype: None
    """
    project_name = PROJECT_NAME
    subject = f'{project_name} - New account for user {username}'
    with open(Path(EMAIL_TEMPLATES_DIR) / 'new_account.html') as f:
        template_str = f.read()
    link = f'{SERVER_HOST_FRONT_END}/verify/?token={uuid}'
    send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={
            'project_name': PROJECT_NAME,
            'username': username,
            'password': password,
            'email': email_to,
            'link': link,
        },
    )


def send_reset_password_email(email_to: str, username: str, password: str, token: str) -> None:
    """
        Reset password for user email send
        :param email_to: Email to user
        :type email_to: str
        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        :param token: Token
        :type token: str
        :return: None
        :rtype: None
    """
    project_name = PROJECT_NAME
    subject = f'{project_name} - Reset password for user {username}'
    with open(Path(EMAIL_TEMPLATES_DIR) / 'reset_password.html') as f:
        template_str = f.read()
    link = f'{SERVER_HOST_FRONT_END}/password-reset/?token={token}'
    send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={
            'project_name': PROJECT_NAME,
            'username': username,
            'password': password,
            'email': email_to,
            'link': link,
        },
    )


def send_username_email(email_to: str, username: str) -> None:
    """
        Send email for get username
        :param email_to: Email
        :type email_to: str
        :param username: Username
        :type username: str
        :return: None
    """
    project_name = PROJECT_NAME
    subject = f'{project_name} - Get username'
    with open(Path(EMAIL_TEMPLATES_DIR) / 'get_username.html') as f:
        template_str = f.read()
    send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={
            'project_name': PROJECT_NAME,
            'username': username,
            'email': email_to,
        },
    )

