import os

from fastapi import HTTPException, status
from fastapi.responses import FileResponse

from config import PAGINATE_SIZE


async def get_file(file_name: str) -> FileResponse:
    """
        Get file
        :param file_name: File name
        :type file_name: str
        :return: File
        :rtype: FileResponse
        :raise HTTPException 404: File not found
    """

    base_dir = 'media/'

    if not os.path.exists(base_dir + file_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='File not found')

    return FileResponse(base_dir + file_name)


def paginate(crud, url):

    def paginate_wrapper(function):

        async def wrapper(*args, **kwargs):
            skip = PAGINATE_SIZE * (kwargs['page'] - 1)
            queryset = await crud.all(skip, PAGINATE_SIZE)

            if not queryset:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Results not found')

            next_page = f'{url}{kwargs["page"] + 1}' if await crud.page_exists(skip + PAGINATE_SIZE, PAGINATE_SIZE) else None
            previous_page = None

            if (kwargs['page'] - 1) > 0:
                previous_page = f'{url}{kwargs["page"] - 1}' if await crud.page_exists(skip - PAGINATE_SIZE, PAGINATE_SIZE) else None

            return {
                'next': next_page,
                'previous': previous_page,
                'page': kwargs['page'],
                'results': await function(*args, queryset=queryset, **kwargs)
            }

        return wrapper

    return paginate_wrapper
