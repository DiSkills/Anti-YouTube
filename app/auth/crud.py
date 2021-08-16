from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from app.CRUD import CRUD
from app.auth.models import User, Verification, Subscriptions
from app.auth.schemas import RegisterUser, UserUpdate, VerificationUUID


class UserCRUD(CRUD[User, RegisterUser, UserUpdate]):
    """ User CRUD """

    async def count_followers(self, db: AsyncSession, pk: int) -> int:
        """
            Followers count
            :param db: DB
            :type db: AsyncSession
            :param pk: Channel ID
            :type pk: int
            :return: Count followers
            :rtype: int
        """
        query = await db.execute(
            select(count(Subscriptions.c.subscription_id).filter(Subscriptions.c.subscription_id == pk))
        )
        return list(query)[0][0]


class VerificationCRUD(CRUD[Verification, VerificationUUID, VerificationUUID]):
    """ Verification CRUD """
    pass


user_crud = UserCRUD(User)
verification_crud = VerificationCRUD(Verification)
