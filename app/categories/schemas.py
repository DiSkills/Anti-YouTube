from pydantic import BaseModel


class CreateCategory(BaseModel):
    """ Create category """

    name: str


class UpdateCategory(CreateCategory):
    """ Update category """

    pass


class GetCategory(CreateCategory):
    """ Get category """

    id: int
