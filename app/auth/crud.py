from app.CRUD import CRUD
from app.auth.models import User, Verification
from app.auth.schemas import RegisterUser, UserUpdate, VerificationUUID


class UserCRUD(CRUD[User, RegisterUser, UserUpdate]):
    """ User CRUD """
    pass


class VerificationCRUD(CRUD[Verification, VerificationUUID, VerificationUUID]):
    """ Verification CRUD """
    pass


user_crud = UserCRUD(User)
verification_crud = VerificationCRUD(Verification)
