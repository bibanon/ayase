#!/usr/bin/python3
# -*- coding: utf-8 -*-

import hug
# use this cookiecutter for packaging
# https://github.com/7ideas/cookiecutter-falcon

# for HTML templating, jinja2 can be used or the falcon integration:
# https://github.com/myuz/falcon-jinja
# https://jinja.palletsprojects.com/en/2.11.x/api/
from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
env = Environment(
#    loader=PackageLoader('ayase', 'templates'),
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


# autogeneration of OpenAPI Swagger docs might be good, but currently not yet supported by Hug
# https://github.com/hugapi/hug/issues/198

# in the future, use ultrajson for speed and forward slash escape if installed, if not just use json
# may still need to wait for support added by hug
# https://github.com/hugapi/hug/issues/846
import os
import io
import json

# The more advanced urllib.request requires python3
import urllib
import urllib.request
import shutil
import tempfile # solely used for caching image files temporarily out of /tmp, not to be used in production

from model.asagi import *

# later use SQL, psycopg2cffi is needed for cython/pypy support
#import psycopg2cffi

# proof of concept is literally just a 4chan API proxy
# https://github.com/4chan/4chan-API/blob/master/pages/Endpoints_and_domains.md
FOURCHAN_BASEAPI = 'a.4cdn.org'

#
# Static urllib request functions
#

# download a file to disk. Not really what we need here though as no cache is necessary.
def download(hostname, endpoint, fname="", file_obj=None):
    # Download the file from `url` and save it locally under `fname`:
    # https://stackoverflow.com/a/7244263
    if fname == "" and file_obj == None:
        print("either fname or file_obj are required")
        return None
    elif fname == "":
        outfile = file_obj
    elif file_obj == None:
        outfile = open(fname, 'wb')
    
    url = "https://%s%s" % (hostname, endpoint)
    
    with urllib.request.urlopen(url) as response, outfile:
        shutil.copyfileobj(response, outfile)
    
    return fname

# make an HTTP GET request to the 4chan API to forward and return a urllib object. Ensure that there is a slash in front of the endpoint, allows it to double as 4chan and hug endpoint.
def get(hostname, endpoint):
    url = "https://%s%s" % (hostname, endpoint)
    response = urllib.request.urlopen(url).read()
    return response

# return a json object
def get_fourchan_json(endpoint, hostname=FOURCHAN_BASEAPI):
    response = get(hostname, endpoint)
    
    return json.loads(response.decode('utf-8'))

# return a raw bytestream
def get_fourchan_file(endpoint, hostname=FOURCHAN_BASEAPI):
    response = get(hostname, endpoint)
    
    return io.BytesIO(response)

#
# JSON API Endpoints
#

# https://github.com/4chan/4chan-API/blob/master/pages/Boards.md
BOARDS_ENDPOINT = '/boards.json'
@hug.get(BOARDS_ENDPOINT)
def boards():
    return get_fourchan_json(
        BOARDS_ENDPOINT
    )

# https://github.com/4chan/4chan-API/blob/master/pages/Catalog.md
THREADLIST_ENDPOINT = '/{board_name}/threads.json'
@hug.get(THREADLIST_ENDPOINT)
def threadlist(board_name:str):
    return get_fourchan_json(
        THREADLIST_ENDPOINT.format(
            board_name=board_name
        )
    )

# https://github.com/4chan/4chan-API/blob/master/pages/Catalog.md
CATALOG_ENDPOINT = '/{board_name}/catalog.json'
@hug.get(CATALOG_ENDPOINT)
def catalog(board_name:str):
    return get_fourchan_json(
        CATALOG_ENDPOINT.format(
            board_name=board_name
        )
    )

# https://github.com/4chan/4chan-API/blob/master/pages/Archive.md
ARCHIVE_ENDPOINT = '/{board_name}/archive.json'
@hug.get(ARCHIVE_ENDPOINT)
def archive(board_name:str):
    return get_fourchan_json(
        ARCHIVE_ENDPOINT.format(
            board_name=board_name
        )
    )

# https://github.com/4chan/4chan-API/blob/master/pages/Archive.md
INDEXES_ENDPOINT = '/{board_name}/{page_num}.json'
@hug.get(INDEXES_ENDPOINT)
def index(board_name:str, page_num:int):
    return get_fourchan_json(
        INDEXES_ENDPOINT.format(
            board_name=board_name,
            page_num=page_num
        )
    )

# https://github.com/4chan/4chan-API/blob/master/pages/Threads.md
THREAD_ENDPOINT = '/{board_name}/thread/{thread_id}.json'
@hug.get(THREAD_ENDPOINT)
def thread(board_name:str, thread_id:int):
    '''Get thread from board'''
    
    # 4chan API appears to escape forward slashes in its outputted text, should we do the same?
    # https://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    # https://github.com/ultrajson/ultrajson/issues/110
    
    # default behavior of ultrajson is to escape forward slashes, set escape_forward_slashes=False if this is not desired
    #return ujson.dumps(data)
    # python json does not escape forward slashes, which might not be fully 4chan API compliant but should work with problems with any JSON parser.
    return get_fourchan_json(
        THREAD_ENDPOINT.format(
            board_name=board_name,
            thread_id=thread_id
        )
    )

#
# Binary data endpoints
# (In practice this should be done more efficiently by Nginx, not this middleware, but its just for completeness in testing as a total proxy)
# set image url to localhost:8000/img/ for both full images and thumbnails
#
# https://github.com/4chan/4chan-API/blob/master/pages/User_images_and_static_content.md

# serve css and fonts from a static endpoint (have nginx do this instead, just for testing purposes only)
@hug.static('/static')
def static_html_dir():
    # must be run from pwd!
    return ['static']

# image endpoint works for thumbnails and full images, because thumbnails just are always s.jpg (have nginx handle url routing like that...)
FOURCHAN_IMAGE_HOST = "i.4cdn.org"
IMAGE_ENDPOINT = '/{board_name}/{img_fname}'
# due to the proxy, we need to put it under img here, but ideally the image server would be separately served from another port

# send file to the user to view
# autodetect to restricted output formats based on suffix
# all output formats listed here:
# https://hugapi.github.io/hug/documentation/OUTPUT_FORMATS/
@hug.get('/img' + IMAGE_ENDPOINT, output=hug.output_format.suffix(
    {
        '.jpg': hug.output_format.image('jpg'),
        '.jpeg': hug.output_format.image('jpg'),
        '.png': hug.output_format.image('png'),
        '.gif': hug.output_format.image('gif'),
        '.webm': hug.output_format.video('webm', hug.Response(), 'read'),
    }
))
def image(board_name:str, img_fname:str):
    # for image from disk:
#    img_file = os.path.join(tempfile.gettempdir(), tfile.name) # type: str
    return get_fourchan_file(
        IMAGE_ENDPOINT.format(
            board_name=board_name,
            img_fname=img_fname
        ),
        hostname=FOURCHAN_IMAGE_HOST
    )

# static file endpoints are not served here, they should be served from a directory as files, and FLOSS alternatives used for each one

#
# HTML endpoints
#
@hug.get('/{board_name}/catalog.html', output=hug.output_format.html)
def catalog_html(board_name:str):
    template = env.get_template('index.html')
    
    # use the existing json hug function to grab the data
    catalog_dict = catalog(board_name)
    
    return template.render(
        pages=catalog_dict,
        board=board_name,
        title="4chan Board Title" # need to somehow extract this from somewhere... or not?
    )

@hug.get('/{board_name}/thread/{thread_id}', output=hug.output_format.html)
def thread_html(board_name:str, thread_id:int):
    template = env.get_template('thread.html')
    
    # use the existing json hug function to grab the data
    thread_dict = thread(board_name, thread_id)
    
    try:
        # title comes from op's subject, use post id instead if not found
        title = thread_dict['posts'][0]['sub']
    except KeyError:
        title = thread_dict['posts'][0]['no']
    
    return template.render(
        posts=thread_dict['posts'],
        board=board_name,
        title=title
    )
