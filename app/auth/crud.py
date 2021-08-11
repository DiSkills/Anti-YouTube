from app.CRUD import CRUD
from app.auth.models import User, Verification


class UserCRUD(CRUD):
    """ User CRUD """
    pass


class VerificationCRUD(CRUD):
    """ Verification CRUD """
    pass


user_crud = UserCRUD(User)
verification_crud = VerificationCRUD(Verification)
