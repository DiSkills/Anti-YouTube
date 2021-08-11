from pydantic import BaseModel, EmailStr, validator


class Password(BaseModel):
    """
        Password
        :type password: str
        :type confirm_password: str
    """

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
    """
        User base
        :type username: str
        :type email: EmailStr
        :type about: str
        :type send_message: bool
    """

    username: str
    email: EmailStr
    about: str
    send_message: bool


class RegisterUser(UserBase, Password):
    """ Register user """

    pass


class VerificationUUID(BaseModel):
    """
        Verification uuid
        :type uuid: str
    """

    uuid: str


class UserUpdate(BaseModel):
    """
        Update user active
        :type is_active: bool
    """

    is_active: bool = True


class LoginUser(BaseModel):
    """
        Login user
        :type username: str
        :type password: str
    """

    username: str
    password: str


class RefreshToken(BaseModel):
    """
        Refresh token
        :type refresh_token: str
    """
    refresh_token: str


class AccessToken(BaseModel):
    """
        Access token
        :type access_token: str
    """
    access_token: str


class Tokens(RefreshToken, AccessToken):
    """
        Login tokens
        :type token_type: str
    """

    token_type: str
