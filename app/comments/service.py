from typing import List, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.comments.crud import comment_crud
from app.comments.models import Comment
from app.comments.schemas import CreateComment
from app.comments.send_emails import send_new_comment_email
from app.videos.crud import video_crud


async def get_children(db: AsyncSession, comments: List[Comment]) -> List[Dict[str, Any]]:
    res = []
    for comment in comments:
        c = {
            'parent_id': list(await db.execute(comment.parent))[0][0].id,
            'id': comment.id,
            'text': comment.text,
            'created_at': comment.created_at,
            'user': comment.user.__dict__,
            'is_child': comment.is_child,
        }

        children = await comment_crud.get_children(db, comment)

        if len(children):
            c['children'] = await get_children(db, children)
        res.append(c)
    return res


async def comment_tree(db: AsyncSession, comments: List[Comment]) -> List[Dict[str, Any]]:
    res = []
    for comment in comments:
        c = {
            'parent_id': None,
            'id': comment.id,
            'text': comment.text,
            'created_at': comment.created_at,
            'user': comment.user.__dict__,
            'is_child': comment.is_child,
        }

        children = await comment_crud.get_children(db, comment)

        if len(children):
            c['children'] = await get_children(db, children)
        if not comment.is_child:
            res.append(c)
    return res


async def create_comment(db: AsyncSession, schema: CreateComment, user: User) -> Dict[str, Any]:
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
        :raise HTTPException 400: Video not found or Parent not found
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

    video = await video_crud.get(db, id=schema.video_id)

    if parent:
        if parent.user.id != user.id:
            send_new_comment_email(
                parent.user.email,
                parent.user,
                video,
                new_comment,
            )
            if (user.id != video.user.id) and (parent.user.id != video.user.id):
                send_new_comment_email(video.user.email, video.user, video, new_comment)
    elif user.id != video.user.id:
        send_new_comment_email(video.user.email, video.user, video, new_comment)

    return {
        **new_comment.__dict__,
        'user': new_comment.user.__dict__,
        'parent': {**parent.__dict__, 'user': parent.user.__dict__} if parent else None,
        'parent_id': parent.id if parent else None,
    }


async def get_comments(db: AsyncSession, pk: int) -> List[Dict[str, Any]]:
    """
        Get comments for video
        :param db: DB
        :type db: AsyncSession
        :param pk: Video ID
        :type pk: int
        :return: Comment tree
        :rtype: list
        :raise HTTPException 400: Video not found
    """

    if not await video_crud.exists(db, id=pk):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video not found')

    comments = await comment_crud.filter(db, video_id=pk)
    return await comment_tree(db, comments)
