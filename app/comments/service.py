from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.comments.crud import comment_crud
from app.comments.schemas import CreateComment
from app.videos.crud import video_crud


async def create_comment(db: AsyncSession, schema: CreateComment, user: User):
    """
        Create comment
        :param db: DB
        :type db: AsyncSession
        :param schema: Schema
        :type schema: CreateComment
        :param user: User
        :type user: User
        :return: Comment
        :rtype: dict
    """

    if not await video_crud.exists(db, id=schema.video_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video not found')

    parent = None

    if schema.parent_id:
        if not await comment_crud.exists(db, id=schema.parent_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Parent not found')
        parent = await comment_crud.get(db, id=schema.parent_id)
        is_child = True
    else:
        is_child = False

    del schema.parent_id
    new_comment = await comment_crud.create(db, schema, user_id=user.id, is_child=is_child)

    if is_child:
        parent.children.append(new_comment)

    return {
        **new_comment.__dict__,
        'user': new_comment.user.__dict__,
        'parent': {**parent.__dict__, 'user': parent.user.__dict__} if parent else None,
    }
