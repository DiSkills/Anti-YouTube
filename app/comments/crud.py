from app.CRUD import CRUD
from app.comments.models import Comment
from app.comments.schemas import CreateComment


class CommentCRUD(CRUD[Comment, CreateComment, CreateComment]):
    """ Comment CRUD """
    pass


comment_crud = CommentCRUD(Comment)
