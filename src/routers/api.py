""" Ayase JSON API routes """

from fastapi import APIRouter, Response, status
from src.core.settings import board_list, archive_list
from src.backend.asagi_converter import (
    convert_thread,
    generate_gallery,
    generate_index
)
router = APIRouter()


@router.get("/{board_name}/catalog.json")
async def gallery(board_name: str, response: Response):
    if board_name in archive_list or board_name in board_list:
        return await generate_gallery(board_name, 1)
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": 404}


@router.get("/{board_name}/thread/{thread_id}.json")
async def thread(board_name: str, thread_id: int, response: Response):
    if board_name in archive_list or board_name in board_list:
        res = await convert_thread(board_name, thread_id)
        if res and len(res) > 0 and res[0].get("posts"):
            return res
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": 404}


@router.get("/{board_name}/{page_num}.json")
async def board_index(board_name: str, page_num: int, response: Response):
    if board_name in archive_list or board_name in board_list:
        res = await generate_index(board_name, page_num, html=False)
        if res and res.get("threads"):
            return res
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": 404}
