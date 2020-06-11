#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import timeit
import yaml
import hug
import sys
from model.asagi import convert_thread, generate_index, convert_post

from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
env = Environment(
#    loader=PackageLoader('ayase', 'templates'),
    loader=FileSystemLoader('foolfuuka/templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

# load the boards list
with open("config.yml", 'r') as yaml_conf:
    CONF = yaml.safe_load(yaml_conf)

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
    
@hug.get('/', output=hug.output_format.html)
def index_html(request):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    template = env.get_template('index.html')
    return template.render(
        archives=archives,
        boards=boards,
        skin=skin,
        skins=skins,
        site_name=site_name,
        index='yes'
    )

@hug.get('/{board_name}/{page_num}.json')
def board_index(board_name:str, page_num:int):
    if(board_name in archive_list or board_name in board_list):
        return generate_index(board_name, page_num, html=False)
    return {'error': 404}

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
            title=title,
            skin=skin,
            skins=skins,
            site_name=site_name,
        )
        end = timeit.default_timer()
        print('Time to generate index: ', end-start, file=sys.stderr)

        return result
    return env.get_template('404.html').render(archives=archives, boards=boards, title='Not Found')

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
            title=title,
            skin=skin,
            skins=skins,
            site_name=site_name,
        )
    return env.get_template('404.html').render(archives=archives, boards=boards, title='Not Found')

@hug.get('/{board_name}/thread/{thread_id}.json')
def thread(board_name:str, thread_id:int):
    if(board_name in archive_list or board_name in board_list):
        return convert_thread(board_name, thread_id)
    return {'error': 404}
    

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
            title = thread_dict['posts'][0]['sub']
        except KeyError:
            title = thread_dict['posts'][0]['no']
            
        except IndexError:
            # no thread was returned
            title = "Not found"
            template = env.get_template('404.html')
            
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
        )
        end = timeit.default_timer()
        print('Time to generate thread: ', end-start, file=sys.stderr)
        
        return result
    return env.get_template('404.html').render()

@hug.get('/{board_name}/posts/{thread_id}', output=hug.output_format.html)
def posts_html(request, board_name:str, thread_id:int):
    if request.get_cookie_values('ayase_skin'):
        skin = request.get_cookie_values('ayase_skin')[0]
    else:
        skin = CONF['default_skin']
    if(board_name in archive_list or board_name in board_list):
        template = env.get_template('posts.html')
        thread_dict, quotelinks = convert_thread(board_name, thread_id)
        
        if(len(thread_dict['posts']) == 0):
            template = env.get_template('404.html')
            return template.render()
        
        #remove OP post     
        del thread_dict['posts'][0]
        
        return template.render(
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
    
    return env.get_template('404.html').render()

@hug.get('/{board_name}/post/{post_id}', output=hug.output_format.html)
def post_html(board_name:str, post_id:int):
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
    return env.get_template('404.html').render()
