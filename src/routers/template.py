#!/usr/bin/python3
# -*- coding: utf-8 -*-
import timeit
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import HTMLResponse

from src.core.settings import (
    config,
    render_constants,
    board_list,
    archive_list
)
from src.backend.asagi_converter import (
    convert_thread,
    generate_index,
    convert_post,
    generate_gallery
)
from ..dependencies import check_admin_cookies, get_skin

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
)

# FastAPI router
router = APIRouter()

env = Environment(
    #    loader=PackageLoader('ayase', 'templates'),
    loader=FileSystemLoader(
        f"src/templates/{config['template_name']}/templates"
    ),
    autoescape=select_autoescape(["html", "xml"]),
)

# Cache templates
template_index = env.get_template("index.html")
template_board_index = env.get_template("board_index.html")
template_404 = env.get_template("404.html")
template_gallery = env.get_template("gallery.html")
template_thread = env.get_template("thread.html")
template_post = env.get_template("post.html")
template_post_sha256 = env.get_template("post_sha256.html")
template_posts = env.get_template("posts.html")


# TODO: Move these to dependencies.py
class NotFoundException(Exception):
    def __init__(self, board_name=config["site_name"]):
        self.title_window = board_name
        if board_name == config["site_name"]:
            return
        board_description = get_board_entry(board_name)["name"]
        title = (
            f"/{board_name}/ - {board_description}"
            if board_description else board_name
        )
        self.title_window = title


async def not_found_exception_handler(
    request: Request,
    exc: NotFoundException
):
    content = template_404.render(
        **render_constants,
        title=exc.title_window,
        title_window=exc.title_window,
        skin=get_skin(request),
        status_code=404
    )
    return HTMLResponse(content=content, status_code=404)


# Find board in list of archives, if not check list of boards, otherwise
# return empty entry
def get_board_entry(board_name: str):
    return next(
        (item for item in (config["archives"] or [])
            if item["shortname"] == board_name),
        next(
            (item for item in (config["boards"] or [])
                if item["shortname"] == board_name),
            {"shortname": "", "name": ""},
        ),
    )


# Order matters
# https://fastapi.tiangolo.com/tutorial/path-params/#order-matters
@router.get("/", response_class=HTMLResponse)
async def index_html(request: Request):
    content = template_index.render(
        **render_constants,
        title=config["site_name"],
        title_window=config["site_name"],
        skin=get_skin(request)
    )
    return content


@router.get("/{board_name}",
            response_class=HTMLResponse,
            dependencies=[Depends(check_admin_cookies)]
            )
async def board_html(request: Request, board_name: str):
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()
        index = await generate_index(board_name, 1)

        if len(index["threads"]) > 0:
            board_description = get_board_entry(board_name)["name"]
            title = f"/{board_name}/ - {board_description}"
            # print(index['threads'][0]['quotelinks'])
            content = template_board_index.render(
                **render_constants,
                page_num=1,
                threads=index["threads"],
                quotelinks=[],
                board=board_name,
                mod=await check_admin_cookies(request),
                image_uri=config["image_location"]["image"].format(
                    board_name=board_name),
                thumb_uri=config["image_location"]["thumb"].format(
                    board_name=board_name),
                title=title,
                title_window=title,
                skin=get_skin(request)
            )
            end = timeit.default_timer()
            if config["debug"]:
                print("Time to generate index: ", end - start)
            return content
    raise NotFoundException(board_name)


@router.get("/{board_name}/gallery",
            response_class=HTMLResponse,
            dependencies=[Depends(check_admin_cookies)]
            )
async def gallery_html(request: Request, board_name: str):
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()
        gallery = await generate_gallery(board_name, 1)

        board_description = get_board_entry(board_name)["name"]
        title = f"/{board_name}/ - {board_description}"
        title_window = title + " » Gallery"
        content = template_gallery.render(
            **render_constants,
            gallery=gallery,
            page_num=1,
            board=board_name,
            mod=await check_admin_cookies(request),
            image_uri=config["image_location"]["image"].format(
                board_name=board_name),
            thumb_uri=config["image_location"]["thumb"].format(
                board_name=board_name),
            title=title,
            title_window=title_window,
            skin=get_skin(request)
        )
        end = timeit.default_timer()
        if config["debug"]:
            print("Time to generate gallery: ", end - start)
        return content
    raise NotFoundException(board_name)


@router.get("/{board_name}/gallery/{page_num}",
            response_class=HTMLResponse,
            dependencies=[Depends(check_admin_cookies)]
            )
async def gallery_index_html(request: Request, board_name: str, page_num: int):
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()
        gallery = await generate_gallery(board_name, page_num)
        board_description = get_board_entry(board_name)["name"]
        title = f"/{board_name}/ - {board_description}"
        title_window = title + f" » Gallery Page {page_num}"
        content = template_gallery.render(
            **render_constants,
            gallery=gallery,
            page_num=page_num,
            board=board_name,
            mod=await check_admin_cookies(request),
            image_uri=config["image_location"]["image"].format(
                board_name=board_name),
            thumb_uri=config["image_location"]["thumb"].format(
                board_name=board_name),
            title=title,
            title_window=title_window,
            skin=get_skin(request),
        )
        end = timeit.default_timer()
        if config["debug"]:
            print("Time to generate gallery: ", end - start)
        return content
    raise NotFoundException(board_name)


@router.get("/{board_name}/page/{page_num}",
            response_class=HTMLResponse,
            dependencies=[Depends(check_admin_cookies)]
            )
async def board_index_html(request: Request, board_name: str, page_num: int):
    if board_name in archive_list or board_name in board_list:
        index = await generate_index(board_name, page_num)
        if len(index["threads"]) > 0:
            board_description = get_board_entry(board_name)["name"]
            title = f"/{board_name}/ - {board_description}"
            title_window = title + f" » Page {page_num}"
            content = template_board_index.render(
                **render_constants,
                page_num=page_num,
                threads=index["threads"],
                quotelinks=[],
                board=board_name,
                mod=await check_admin_cookies(request),
                image_uri=config["image_location"]["image"].format(
                    board_name=board_name),
                thumb_uri=config["image_location"]["thumb"].format(
                    board_name=board_name),
                title=title,
                title_window=title_window,
                skin=get_skin(request)
            )
            return content
    raise NotFoundException(board_name)


@router.get("/{board_name}/thread/{thread_id}",
            response_class=HTMLResponse,
            dependencies=[Depends(check_admin_cookies)]
            )
async def thread_html(request: Request, board_name: str, thread_id: int):
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()

        # use the existing json app function to grab the data
        thread_dict, quotelinks = await convert_thread(board_name, thread_id)

        title = f"/{board_name}/"
        try:
            # title comes from op's subject, use post id instead if not found
            subject_title = thread_dict["posts"][0]["sub"]
            board_description = get_board_entry(board_name)["name"]
            title = f"/{board_name}/ - {board_description}"
            title_window = (
                title
                + (f" - {subject_title}" if subject_title else "")
                + f" » Thread #{thread_id} - {config['site_name']}"
            )
        except IndexError:
            # no thread was returned
            raise NotFoundException(board_name)

        content = template_thread.render(
            **render_constants,
            posts=thread_dict["posts"],
            quotelinks=quotelinks,
            board=board_name,
            mod=await check_admin_cookies(request),
            image_uri=config["image_location"]["image"].format(
                board_name=board_name),
            thumb_uri=config["image_location"]["thumb"].format(
                board_name=board_name),
            title=title,
            title_window=title_window,
            skin=get_skin(request)
        )
        end = timeit.default_timer()
        if config["debug"]:
            print("Time to generate thread: ", end - start)
        return content
    raise NotFoundException(board_name)


@router.get("/{board_name}/posts/{thread_id}",
            response_class=HTMLResponse,
            dependencies=[Depends(check_admin_cookies)]
            )
async def posts_html(request: Request, board_name: str, thread_id: int):
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()
        thread_dict, quotelinks = await convert_thread(board_name, thread_id)

        if len(thread_dict["posts"]) > 0:
            # remove OP post
            del thread_dict["posts"][0]

            content = template_posts.render(
                **render_constants,
                posts=thread_dict["posts"],
                quotelinks=quotelinks,
                board=board_name,
                image_uri=config["image_location"]["image"].format(
                    board_name=board_name),
                thumb_uri=config["image_location"]["thumb"].format(
                    board_name=board_name),
                skin=get_skin(request),
            )
            end = timeit.default_timer()
            if config["debug"]:
                print("Time to generate posts: ", end - start)
            return content
    raise NotFoundException(board_name)


@router.get("/{board_name}/post/{post_id}",
            response_class=HTMLResponse,
            dependencies=[Depends(check_admin_cookies)]
            )
async def post_html(
    request: Request, board_name: str, post_id: int, response: Response
):
    if board_name in archive_list or board_name in board_list:

        post = await convert_post(board_name, post_id)

        # Switch to SHA256 template if hash option is set
        template = template_post
        if render_constants["sha256_dirs"]:
            template = template_post_sha256

        if len(post) > 0:
            # set resto to a non zero value to prevent the template
            # from rendering OPs with the format of an OP post
            if post["resto"] == 0:
                post["resto"] = -1

            content = template.render(
                **render_constants,
                post=post,
                board=board_name,
                image_uri=config["image_location"]["image"].format(
                    board_name=board_name),
                thumb_uri=config["image_location"]["thumb"].format(
                    board_name=board_name),
                skin=get_skin(request),
                quotelink=True,
            )
            return content
    raise NotFoundException(board_name)
