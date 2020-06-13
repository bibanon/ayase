#!/usr/bin/python3
# -*- coding: utf-8 -*-

import timeit
import yaml
import sys
from fastapi import FastAPI, Request, Response, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, ORJSONResponse

from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape


global app
app = FastAPI()


def custom_openapi(openapi_prefix: str):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Ayase",
        version="0.1.0",
        description="The Ayase Imageboard Archival Standard",
        routes=app.routes,
        openapi_prefix=openapi_prefix,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://c4.wallpaperflare.com/wallpaper/530/77/135/anime-yotsuba-fuuka-ayase-mr-koiwai-yotsuba-wallpaper-preview.jpg"
        # "url": "https://c4.wallpaperflare.com/wallpaper/487/5/317/anime-yotsuba-fuuka-ayase-wallpaper-preview.jpg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

env = Environment(
    #    loader=PackageLoader('ayase', 'templates'),
    loader=FileSystemLoader("foolfuuka/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

# load the boards list
global CONF
with open("config.yml", "r") as yaml_conf:
    CONF = yaml.safe_load(yaml_conf)

debug = CONF["debug"]

archives = CONF["archives"]
archive_list = []

boards = CONF["boards"]
skins = CONF["skins"]
site_name = CONF["site_name"]
scraper = CONF["scraper"]
board_list = []

image_uri = CONF["image_location"]["image"]
thumb_uri = CONF["image_location"]["thumb"]
DB_ENGINE = CONF["database"]["default"]

# This has to be here so the variables above are loaded prior to importing these
from model.asagi import convert_thread, generate_index, convert_post, generate_gallery


if boards:
    for i in boards:
        board_list.append(i["shortname"])

for i in archives:
    archive_list.append(i["shortname"])


class NotFoundException(Exception):
    def __init__(self):
        pass


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return HTMLResponse(
        content=env.get_template("404.html").render(
            archives=archives,
            boards=boards,
            title=CONF["site_name"],
            status_code=404,
            scraper=scraper
        )
    )


# Order matters
# https://fastapi.tiangolo.com/tutorial/path-params/#order-matters
@app.get("/", response_class=HTMLResponse)
async def index_html(request: Request):
    try:
        skin = request.cookies.get("ayase_skin")
    except:
        skin = CONF["default_skin"]
    template = env.get_template("index.html")
    return HTMLResponse(
        content=template.render(
            title=CONF["site_name"],
            archives=archives,
            boards=boards,
            skin=skin,
            skins=skins,
            site_name=site_name,
            index="yes",
            options=CONF["options"],
            scraper=scraper,
        ),
        status_code=200,
    )
    raise NotFoundException()


@app.get("/{board_name}", response_class=HTMLResponse)
async def board_html(request: Request, board_name: str):
    if request.cookies.get("ayase_skin"):
        skin = request.cookies.get("ayase_skin")
    else:
        skin = CONF["default_skin"]
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()

        template = env.get_template("board_index.html")

        index = await generate_index(board_name, 1)

        if len(index["threads"]) > 0:
            title = board_name
            # print(index['threads'][0]['quotelinks'])
            result = template.render(
                asagi=True,
                page_num=1,
                threads=index["threads"],
                quotelinks=[],
                archives=archives,
                board=board_name,
                boards=boards,
                image_uri=image_uri.format(board_name=board_name),
                thumb_uri=thumb_uri.format(board_name=board_name),
                options=CONF["options"],
                title=title,
                skin=skin,
                skins=skins,
                site_name=site_name,
                scraper=scraper
            )
            end = timeit.default_timer()
            if debug:
            	print("Time to generate index: ", end - start)
            return HTMLResponse(content=result, status_code=200)
    raise NotFoundException()


@app.get("/{board_name}/catalog.json", response_class=ORJSONResponse)
async def gallery(board_name: str, response: Response):
    if board_name in archive_list or board_name in board_list:
        return await generate_gallery(board_name, 1)
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": 404}


@app.get("/{board_name}/gallery", response_class=HTMLResponse)
async def gallery_html(request: Request, board_name: str):
    if request.cookies.get("ayase_skin"):
        skin = request.cookies.get("ayase_skin")
    else:
        skin = CONF["default_skin"]
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()
        gallery = await generate_gallery(board_name, 1)

        template = env.get_template("gallery.html")
        result = template.render(
            asagi=True,
            gallery=gallery,
            page_num=1,
            archives=archives,
            board=board_name,
            boards=boards,
            image_uri=image_uri.format(board_name=board_name),
            thumb_uri=thumb_uri.format(board_name=board_name),
            title=board_name,
            options=CONF["options"],
            skin=skin,
            skins=skins,
            scraper=scraper
        )
        end = timeit.default_timer()
        if debug:
            print("Time to generate gallery: ", end - start)
        return HTMLResponse(content=result, status_code=200)
    raise NotFoundException()


@app.get("/{board_name}/gallery/{page_num}", response_class=HTMLResponse)
async def gallery_index_html(request: Request, board_name: str, page_num: int):
    if request.cookies.get("ayase_skin"):
        skin = request.cookies.get("ayase_skin")
    else:
        skin = CONF["default_skin"]
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()
        gallery = await generate_gallery(board_name, page_num)

        template = env.get_template("gallery.html")
        result = template.render(
            asagi=True,
            gallery=gallery,
            page_num=page_num,
            archives=archives,
            board=board_name,
            boards=boards,
            image_uri=image_uri.format(board_name=board_name),
            thumb_uri=thumb_uri.format(board_name=board_name),
            title=board_name,
            options=CONF["options"],
            skin=skin,
            skins=skins,
            scraper=scraper
        )
        end = timeit.default_timer()
        if debug:
            print("Time to generate gallery: ", end - start)
        return HTMLResponse(content=result, status_code=200)
    raise NotFoundException()

@app.get("/{board_name}/page/{page_num}", response_class=HTMLResponse)
async def board_index_html(request: Request, board_name: str, page_num: int):
    if request.cookies.get("ayase_skin"):
        skin = request.cookies.get("ayase_skin")
    else:
        skin = CONF["default_skin"]
    if board_name in archive_list or board_name in board_list:
        template = env.get_template("board_index.html")

        index = await generate_index(board_name, page_num)

        if len(index["threads"]) > 0:
            title = board_name
            return HTMLResponse(
                content=template.render(
                    asagi=True,
                    page_num=page_num,
                    threads=index["threads"],
                    quotelinks=[],
                    archives=archives,
                    board=board_name,
                    boards=boards,
                    image_uri=image_uri.format(board_name=board_name),
                    thumb_uri=thumb_uri.format(board_name=board_name),
                    options=CONF["options"],
                    title=title,
                    skin=skin,
                    skins=skins,
                    site_name=site_name,
                    scraper=scraper
                ),
                status_code=200,
            )
    raise NotFoundException()


@app.get("/{board_name}/thread/{thread_id}.json")
async def thread(board_name: str, thread_id: int, response: Response):
    if board_name in archive_list or board_name in board_list:
    	res = await convert_thread(board_name, thread_id)
    	if res and len(res) > 0 and res[0].get('posts'):
            return res
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": 404}


@app.get("/{board_name}/thread/{thread_id}", response_class=HTMLResponse)
async def thread_html(request: Request, board_name: str, thread_id: int):
    if request.cookies.get("ayase_skin"):
        skin = request.cookies.get("ayase_skin")
    else:
        skin = CONF["default_skin"]
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()

        template = env.get_template("thread.html")

        # use the existing json app function to grab the data
        thread_dict, quotelinks = await convert_thread(board_name, thread_id)

        try:
            # title comes from op's subject, use post id instead if not found
            temp = thread_dict["posts"][0]["sub"]
        except IndexError:
            # no thread was returned
            raise NotFoundException()

        title = board_name
        result = template.render(
            asagi=True,
            posts=thread_dict["posts"],
            quotelinks=quotelinks,
            archives=archives,
            board=board_name,
            boards=boards,
            image_uri=image_uri.format(board_name=board_name),
            thumb_uri=thumb_uri.format(board_name=board_name),
            title=title,
            skin=skin,
            skins=skins,
            site_name=site_name,
            options=CONF["options"],
            scraper=scraper
        )
        end = timeit.default_timer()
        if debug:
            print("Time to generate thread: ", end - start)

        return HTMLResponse(content=result, status_code=200)
    raise NotFoundException()


@app.get("/{board_name}/posts/{thread_id}", response_class=HTMLResponse)
async def posts_html(request: Request, board_name: str, thread_id: int):
    if request.cookies.get("ayase_skin"):
        skin = request.cookies.get("ayase_skin")
    else:
        skin = CONF["default_skin"]
    if board_name in archive_list or board_name in board_list:
        start = timeit.default_timer()

        template = env.get_template("posts.html")
        thread_dict, quotelinks = await convert_thread(board_name, thread_id)

        if len(thread_dict["posts"]) > 0:
            # remove OP post
            del thread_dict["posts"][0]

            result = template.render(
                asagi=True,
                posts=thread_dict["posts"],
                quotelinks=quotelinks,
                board=board_name,
                image_uri=image_uri.format(board_name=board_name),
                thumb_uri=thumb_uri.format(board_name=board_name),
                skin=skin,
                skins=skins,
                site_name=site_name,
                scraper=scraper
            )
            end = timeit.default_timer()
            if debug:
            	print("Time to generate posts: ", end - start)
            return HTMLResponse(content=result, status_code=200)
    raise NotFoundException()


@app.get("/{board_name}/post/{post_id}", response_class=HTMLResponse)
async def post_html(request: Request, board_name: str, post_id: int, response: Response):
    if request.cookies.get("ayase_skin"):
        skin = request.cookies.get("ayase_skin")
    else:
        skin = CONF["default_skin"]
    if board_name in archive_list or board_name in board_list:
        template = env.get_template("post.html")

        post = await convert_post(board_name, post_id)

        if len(post) > 0:
	        if post["resto"] == 0:
	            post["resto"] = -1
	        return HTMLResponse(
	            content=template.render(
	                asagi=True,
	                post=post,
	                board=board_name,
	                image_uri=image_uri.format(board_name=board_name),
	                thumb_uri=thumb_uri.format(board_name=board_name),
	                quotelink=True,
	                scraper=scraper
	            ),
	            status_code=200,
	        )
    raise NotFoundException()

@app.get("/{board_name}/{page_num}.json")
async def board_index(board_name: str, page_num: int, response: Response):
    if board_name in archive_list or board_name in board_list:
    	res = await generate_index(board_name, page_num, html=False)
    	if res and res.get('threads', None):
	        return res 
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": 404}
