from pathlib import Path

from app.auth.models import User
from app.comments.models import Comment
from app.config import SERVER_HOST_FRONT_END, PROJECT_NAME, EMAIL_TEMPLATES_DIR
from app.send_emails import send_email
from app.videos.models import Video


def send_new_comment_email(email_to: str, author: User, video: Video, comment: Comment) -> None:
    """
        Send new comment email
        :param email_to: Email to user
        :type email_to: str
        :param author: Author
        :type author: User
        :param video: Video
        :type video: Video
        :param comment: Comment
        :type comment: Comment
        :return: None
        :rtype: None
    """
    if not author.send_message:
        return

    project_name = PROJECT_NAME
    subject = f'{project_name} - New comment'
    with open(Path(EMAIL_TEMPLATES_DIR) / 'new_comment.html') as f:
        template_str = f.read()
    link = f'{SERVER_HOST_FRONT_END}/videos/{video.id}'
    send_email.delay(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={
            'project_name': PROJECT_NAME,
            'link': link,
            'author': author.username,
            'video': video.title,
            'comment': comment.text,
            'comment_user': comment.user.username,
        },
    )
