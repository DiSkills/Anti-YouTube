from sqlalchemy import Column, String

from app.db import Base, ModelMixin


class Category(Base, ModelMixin):
    """ Category """

    name: str = Column(String)

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'Category {self.name}'
