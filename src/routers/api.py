""" Ayase JSON API routes """
from typing import List, Optional, Union
from pydantic import BaseModel
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from src.core.settings import board_list, archive_list
from src.backend.asagi_converter import (
    convert_thread,
    generate_gallery,
    generate_index
)
router = APIRouter()

class Post(BaseModel):
    no: int = 4042624
    closed: int = 0
    now: str = "02/11/22(Fri)06:01:47"
    name: str = "Anonymous"
    sticky: int = 0
    sub: str = "Lain Thread Layer 124: Powered by CoplandOS"
    w: Optional[int] = 500
    h: Optional[int] = 357
    tn_w: Optional[int] = 250
    tn_h: Optional[int] = 178
    time: int = 1644577307
    asagi_preview_filename: Optional[str] = "1644595307853s.jpg"
    asagi_filename: Optional[str] = "1644595307853.png"
    tim: str = "1644595307853"
    md5: Optional[str] = "dfYGkvF04lbrH2SrZCIiLw=="
    fsize: Optional[int] = 170614
    filename: Optional[str] = "1384669273"
    ext: Optional[str] = "png"
    resto: int = 0
    capcode: Optional[str] = None
    trip: Optional[str] = None
    spoiler: int = 0
    country: Optional[str] = None
    filedeleted: int = 0
    exif: str = "{\"uniqueIps\":\"30\"}"
    com: Optional[str] = "Old Thread:\n>>4027469"
    replies: Optional[int] = 96
    images: Optional[int] = 95

class CatalogResponse(BaseModel):
    page: int
    threads: List[Post]

class ThreadResponse(BaseModel):
    posts: List[Post]

class BoardIndexResponse(BaseModel):
    threads: List[ThreadResponse]

@router.get("/{board_name}/catalog.json", response_model=List[CatalogResponse], responses={404: {"model": None}})
async def gallery(board_name: str, response: Response):
    if board_name in archive_list or board_name in board_list:
        return await generate_gallery(board_name, 1)
    response.status_code = status.HTTP_404_NOT_FOUND
    return JSONResponse(status_code=404, content={"error": 404})


@router.get("/{board_name}/thread/{thread_id}.json", response_model=List[ThreadResponse], responses={404: {"model": None}})
async def thread(board_name: str, thread_id: int, response: Response):
    if board_name in archive_list or board_name in board_list:
        res = await convert_thread(board_name, thread_id)
        if res and len(res) > 0 and res[0].get("posts"):
            return res
    response.status_code = status.HTTP_404_NOT_FOUND
    return JSONResponse(status_code=404, content={"error": 404})


@router.get("/{board_name}/{page_num}.json", response_model=BoardIndexResponse, responses={404: {"model": None}})
async def board_index(board_name: str, page_num: int, response: Response):
    if board_name in archive_list or board_name in board_list:
        res = await generate_index(board_name, page_num, html=False)
        if res and res.get("threads"):
            return res
    response.status_code = status.HTTP_404_NOT_FOUND
    return JSONResponse(status_code=404, content={"error": 404})
