from pydantic import BaseModel, EmailStr, validator


class Password(BaseModel):
    """ Password """

    password: str
    confirm_password: str

    @validator('password')
    def validate_password(cls, password):
        if len(password) < 8:
            raise ValueError('Min length password is 8 chars')
        return password

    @validator('confirm_password')
    def validate_confirm_password(cls, confirm_password, values, **kwargs):
        if 'password' in values and confirm_password != values['password']:
            raise ValueError('Passwords do not match')
        return confirm_password


class UserBase(BaseModel):
    """ User base """

    username: str
    email: EmailStr
    about: str
    send_message: bool


class RegisterUser(UserBase, Password):
    """ Register user """

    pass


class VerificationUUID(BaseModel):
    """ Verification uuid """

    uuid: str


class UserUpdate(BaseModel):
    """ Update user active """

    is_active: bool = True


class LoginUser(BaseModel):
    """ Login user """

    username: str
    password: str


class RefreshToken(BaseModel):
    """ Refresh token """

    refresh_token: str


class AccessToken(BaseModel):
    """ Access token """

    access_token: str


class Tokens(RefreshToken, AccessToken):
    """ Login tokens """

    token_type: str


class TokenPayload(BaseModel):
    """ Token payload """

    user_id: int


class ChangeUserData(BaseModel):
    """ Change user data """

    about: str
    send_message: bool = True


class ChangeUserDataResponse(ChangeUserData):
    """ Change user data response """

    avatar: str
