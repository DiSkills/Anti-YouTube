from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(password: str, hash_password: str) -> bool:
    """
        Verification password
        :param password: Password
        :type password: str
        :param hash_password: Hash
        :type hash_password: str
        :return: Password match?
        :rtype: bool
    """
    return pwd_context.verify(password, hash_password)


def get_password_hash(password: str) -> str:
    """
        Get hash
        :param password: Password
        :type password: str
        :return: Hash
        :rtype: str
    """
    return pwd_context.hash(password)
