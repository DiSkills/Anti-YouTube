from app.CRUD import CRUD
from app.categories.models import Category
from app.categories.schemas import CreateCategory, UpdateCategory


class CategoryCRUD(CRUD[Category, CreateCategory, UpdateCategory]):
    """ Category CRUD """
    pass


category_crud = CategoryCRUD(Category)
