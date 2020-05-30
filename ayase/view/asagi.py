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

board_data = ({'shortname': 'g', 'name': 'Technology'},{'shortname': 'a', 'name': 'Anime & Manga'},{'shortname': 'jp', 'name': 'jp'},{'shortname': 'int', 'name': 'int'},{'shortname': 'ck', 'name': 'Cooking'}, {'shortname': 'pol', 'name': 'Politically Incorrect'}, {'shortname': 'p', 'name': 'Photography'})
board_list = []

for i in board_data:
    board_list.append(i['shortname'])

@hug.get('/{board_name}/{page_num}.json')
def index(board_name:str, page_num:int):
    if(board_name in board_list):
        return generate_index(board_name, page_num)
    return {'error': 404}

@hug.get('/{board_name}', output=hug.output_format.html)
def index_html(board_name:str):
    if(board_name in board_list):
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
            boards=board_data,
            title=title,
            skin='default'
        )
        end = timeit.default_timer()
        print('Time to generate index: ', end-start, file=sys.stderr)

        return result
    return env.get_template('404.html').render()

@hug.get('/{board_name}/page/{page_num}', output=hug.output_format.html)
def index_html(board_name:str, page_num:int):
    if(board_name in board_list):
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
            boards=board_data,
            title=title,
            skin='default'
        )
    return env.get_template('404.html').render()

@hug.get('/{board_name}/thread/{thread_id}.json')
def thread(board_name:str, thread_id:int):
    if(board_name in board_list):
        return convert_thread(board_name, thread_id)
    return {'error': 404}
    

@hug.get('/{board_name}/thread/{thread_id}', output=hug.output_format.html)
def thread_html(board_name:str, thread_id:int, skin="default"):
    if(board_name in board_list):
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
            boards=board_data,
            title=title,
            skin=skin
        )
        end = timeit.default_timer()
        print('Time to generate thread: ', end-start, file=sys.stderr)
        
        return result
    return env.get_template('404.html').render()

@hug.get('/{board_name}/posts/{thread_id}', output=hug.output_format.html)
def posts_html(board_name:str, thread_id:int, skin="default"):
    if(board_name in board_list):
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
            skin=skin
        )
    
    return env.get_template('404.html').render()

@hug.get('/{board_name}/post/{post_id}', output=hug.output_format.html)
def post_html(board_name:str, post_id:int, skin="default"):
    if(board_name in board_list):
        template = env.get_template('post.html')
        
        post = convert_post(board_name, post_id)
        
        if(len(post) == 0):
            template = env.get_template('404.html')
        
        return template.render(
            reply=post,
            board=board_name
        )
    return env.get_template('404.html').render()
