import aiofiles

from fastapi import UploadFile

import os


async def write_file(file_name: str, file: UploadFile) -> None:
    """
        Write file
        :param file_name: File name
        :type file_name: str
        :param file: File
        :type file: UploadFile
        :return: None
    """
    async with aiofiles.open(file_name, 'wb') as buffer:
        data = await file.read()
        await buffer.write(data)


def remove_file(file_name: str) -> None:
    """
        Remove file
        :param file_name: File name
        :type file_name: str
        :return: None
    """

    if os.path.exists(file_name):
        os.remove(file_name)
