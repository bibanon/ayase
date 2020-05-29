#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import timeit
import hug
import sys
from model.asagi import convert_thread, generate_index, convert_post

from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
env = Environment(
#    loader=PackageLoader('ayase', 'templates'),
    loader=FileSystemLoader('foolfuuka/templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

#
# Used for development, should be served with nginx
#
TEMPLATE_STATIC_CONTENT = 'foolfuuka/static/'
@hug.get('/static/{filename}.css', output=hug.output_format.html)
def get_static(filename:str):
    with open(TEMPLATE_STATIC_CONTENT + filename, 'r') as f:
        return f.read()

@hug.get('/static/fontawesome/css/{filename}', output=hug.output_format.html)
def get_fontawesome_static(filename:str):
    with open(TEMPLATE_STATIC_CONTENT + filename, 'r') as f:
        return f.read()

@hug.get('/{board_name}.json')
def index(board_name:str):
    return

@hug.get('/{board_name}', output=hug.output_format.html)
def index_html(board_name:str):
    
    start = timeit.default_timer()

    template = env.get_template('index.html')
    
    index = generate_index(board_name, 1)
    
    if(len(index['threads']) == 0):
        template = env.get_template('404.html')
    title = board_name
    result =  template.render(
        asagi=True,
        page_num=1,
        threads=index['threads'],
        #quotelinks=quotelinks,
        board=board_name,
        title=title,
        skin='default'
    )
    end = timeit.default_timer()
    print('Time to generate index: ', end-start, file=sys.stderr)

    return result

@hug.get('/{board_name}/page/{page_num}', output=hug.output_format.html)
def index_html(board_name:str, page_num:int):
    template = env.get_template('index.html')
    
    index = generate_index(board_name, page_num)
    
    if(len(index['threads']) == 0):
        template = env.get_template('404.html')
        
    title = board_name
    return template.render(
        asagi=True,
        page_num=page_num,
        threads=index['threads'],
        #quotelinks=quotelinks,
        board=board_name,
        title=title,
        skin='default'
    )

@hug.get('/{board_name}/thread/{thread_id}.json')
def thread(board_name:str, thread_id:int):
    return convert_thread(board_name, thread_id)
    

@hug.get('/{board_name}/thread/{thread_id}', output=hug.output_format.html)
def thread_html(board_name:str, thread_id:int, skin="default"):
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
        board=board_name,
        title=title,
        skin=skin
    )
    end = timeit.default_timer()
    print('Time to generate thread: ', end-start, file=sys.stderr)
    
    return result

@hug.get('/{board_name}/posts/{thread_id}', output=hug.output_format.html)
def posts_html(board_name:str, thread_id:int, skin="default"):
    template = env.get_template('posts.html')
    thread_dict, quotelinks = convert_thread(board_name, thread_id)
    
    if(len(thread_dict['posts']) == 0):
        template = env.get_template('404.html')
        return template.render()
    
    #remove OP post     
    del thread_dict['posts'][0]
    
    return template.render(
        posts=thread_dict['posts'],
        board=board_name
    )

@hug.get('/{board_name}/post/{post_id}', output=hug.output_format.html)
def post_html(board_name:str, post_id:int, skin="default"):
    template = env.get_template('post.html')
    
    post = convert_post(board_name, post_id)
    
    if(len(post) == 0):
        template = env.get_template('404.html')
    
    return template.render(
        reply=post,
        board=board_name
    )
