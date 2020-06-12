#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import timeit
import json
import hug
import sys
from falcon import HTTP_404
from model.asagi import convert_thread, generate_index, convert_post, generate_gallery

from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
env = Environment(
#    loader=PackageLoader('ayase', 'templates'),
    loader=FileSystemLoader('foolfuuka/templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

# load the boards list
with open("config.json", 'r') as json_conf:
    CONF = json.load(json_conf)

archives = CONF['archives']
archive_list = []

boards = CONF['boards']
skins = CONF['skins']
site_name = CONF['site_name']
board_list = []

image_uri = CONF['image_location']['image']
thumb_uri = CONF['image_location']['thumb']

for i in boards:
    board_list.append(i['shortname'])
    
for i in archives:
    archive_list.append(i['shortname'])
    
    
#404
@hug.not_found(output=hug.output_format.html)
def not_found_handler():
    return env.get_template('404.html').render(archives=archives, boards=boards, title=CONF['site_name'], options=CONF['options'])

@hug.get('/', output=hug.output_format.html)
def index_html(request):
    try:
        request.get_cookie_values('ayase_skin')
        skin = request.get_cookie_values('ayase_skin')[0]
    except TypeError:
        skin = CONF['default_skin']
    template = env.get_template('index.html')
    return template.render(
        title=CONF['site_name'],
        archives=archives,
        boards=boards,
        skin=skin,
        skins=skins,
        site_name=site_name,
        index='yes',
        options=CONF['options']
    )

@hug.get('/{board_name}/{page_num}.json')
def board_index(board_name:str, page_num:int):
    if(board_name in archive_list or board_name in board_list):
        return generate_index(board_name, page_num, html=False)
    response.status = HTTP_404

@hug.get('/{board_name}', output=hug.output_format.html)
def board_index_html(request, board_name:str):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        start = timeit.default_timer()

        template = env.get_template('board_index.html')
        
        index = generate_index(board_name, 1)
        
        if(len(index['threads']) == 0):
            template = env.get_template('404.html')
        title = board_name
        #print(index['threads'][0]['quotelinks'])
        result = template.render(
            asagi=True,
            page_num=1,
            threads=index['threads'],
            quotelinks=[],
            archives=archives,
            board=board_name,
            boards=boards,
            image_uri=image_uri.format(board_name=board_name),
            thumb_uri=thumb_uri.format(board_name=board_name),
            options=CONF['options'],
            title=title,
            skin=skin,
            skins=skins,
            site_name=site_name,
        )
        end = timeit.default_timer()
        print('Time to generate index: ', end-start)

        return result
    return not_found_handler()

@hug.get('/{board_name}/page/{page_num}', output=hug.output_format.html)
def board_index_html(request, board_name:str, page_num:int):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        template = env.get_template('board_index.html')
        
        index = generate_index(board_name, page_num)
        
        if(len(index['threads']) == 0):
            template = env.get_template('404.html')
            
        title = board_name
        return template.render(
            asagi=True,
            page_num=page_num,
            threads=index['threads'],
            quotelinks=[],
            archives=archives,
            board=board_name,
            boards=boards,
            image_uri=image_uri.format(board_name=board_name),
            thumb_uri=thumb_uri.format(board_name=board_name),
            options=CONF['options'],
            title=title,
            skin=skin,
            skins=skins,
            site_name=site_name,
        )
    return not_found_handler()

@hug.get('/{board_name}/thread/{thread_id}.json')
def thread(board_name:str, thread_id:int):
    if(board_name in archive_list or board_name in board_list):
        return convert_thread(board_name, thread_id)
    response.status = HTTP_404
    

@hug.get('/{board_name}/thread/{thread_id}', output=hug.output_format.html)
def thread_html(request, board_name:str, thread_id:int):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        start = timeit.default_timer()
        
        template = env.get_template('thread.html')
        
        # use the existing json hug function to grab the data
        thread_dict, quotelinks = convert_thread(board_name, thread_id)
        
        try:
            # title comes from op's subject, use post id instead if not found
            temp = thread_dict['posts'][0]['sub']
        except IndexError:
            # no thread was returned
            not_found_handler()
        
        title = board_name
        result = template.render(
            asagi=True,
            posts=thread_dict['posts'],
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
            options=CONF['options']
        )
        end = timeit.default_timer()
        print('Time to generate thread: ', end-start)
        
        return result
    return not_found_handler()

@hug.get('/{board_name}/posts/{thread_id}', output=hug.output_format.html)
def posts_html(request, board_name:str, thread_id:int):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        start = timeit.default_timer()
        
        template = env.get_template('posts.html')
        thread_dict, quotelinks = convert_thread(board_name, thread_id)
        
        if(len(thread_dict['posts']) == 0):
            template = env.get_template('404.html')
            return template.render()
        
        #remove OP post     
        del thread_dict['posts'][0]
        
        result = template.render(
            asagi=True,
            posts=thread_dict['posts'],
            quotelinks=quotelinks,
            board=board_name,
            image_uri=image_uri.format(board_name=board_name),
            thumb_uri=thumb_uri.format(board_name=board_name),
            skin=skin,
            skins=skins,
            site_name=site_name,
        )
        end = timeit.default_timer()
        print('Time to generate posts: ', end-start)
        
        return result
    return not_found_handler()

@hug.get('/{board_name}/post/{post_id}', output=hug.output_format.html)
def post_html(request, board_name:str, post_id:int):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        template = env.get_template('post.html')
        
        post = convert_post(board_name, post_id)
        
        if(len(post) == 0):
            template = env.get_template('404.html')
            
        if(post['resto'] == 0):
            post['resto'] = -1
        
        return template.render(
            asagi=True,
            post=post,
            board=board_name,
            image_uri=image_uri.format(board_name=board_name),
            thumb_uri=thumb_uri.format(board_name=board_name),
            quotelink=True
        )
    return not_found_handler()

@hug.get('/{board_name}/catalog.json')
def gallery(board_name:str, response):
    if(board_name in archive_list or board_name in board_list):
        return generate_gallery(board_name, 1)
    response.status = HTTP_404

@hug.get('/{board_name}/gallery', output=hug.output_format.html)
def gallery_html(request, board_name:str):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        start = timeit.default_timer()
        gallery = generate_gallery(board_name, 1)
        
        template = env.get_template('gallery.html')
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
            options=CONF['options'],
            skin=skin,
            skins=skins
        )
        end = timeit.default_timer()
        print('Time to generate gallery: ', end-start)
        return result
    return not_found_handler()

@hug.get('/{board_name}/gallery/{page_num}', output=hug.output_format.html)
def gallery_html(request, board_name:str, page_num:int):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        start = timeit.default_timer()
        gallery = generate_gallery(board_name, page_num)
        
        template = env.get_template('gallery.html')
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
            options=CONF['options'],
            skin=skin,
            skins=skins
        )
        end = timeit.default_timer()
        print('Time to generate gallery: ', end-start)
        return result
    return not_found_handler()
