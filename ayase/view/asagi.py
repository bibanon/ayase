#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import hug
from model.asagi import convert

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


@hug.get('/{board_name}/thread/{thread_id}.json')
def thread(board_name:str, thread_id:int):
    return convert(board_name, thread_id)
    

@hug.get('/{board_name}/thread/{thread_id}', output=hug.output_format.html)
def thread_html(board_name:str, thread_id:int, skin="default"):
    template = env.get_template('thread.html')
    
    # use the existing json hug function to grab the data
    thread_dict, quotelinks = convert(board_name, thread_id)
    
    try:
        # title comes from op's subject, use post id instead if not found
        title = thread_dict['posts'][0]['sub']
    except KeyError:
        title = thread_dict['posts'][0]['no']
        
    except IndexError:
        # no thread was returned
        title = "Not found"
        template = env.get_template('404.html')
    
    return template.render(
        asagi=True,
        posts=thread_dict['posts'],
        quotelinks=quotelinks,
        board=board_name,
        title=title,
        skin=skin
    )

#def thread_html(board_name:str, thread_num:int):
    #template = env.get_template('thread.html')
    
    #thread = get_thread(board_name, thread_num)
    
    #try:
        ## title comes from op's subject, use post id instead if not found
        #title = thread[0]['title']
    #except:
        #print("Missing title!")
        #title = ''
    
    #return template.render(
        #posts=thread,
        #board=board_name,
        #title=title
    #)
