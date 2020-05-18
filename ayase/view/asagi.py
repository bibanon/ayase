#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from model.asagi import convert

from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
env = Environment(
#    loader=PackageLoader('ayase', 'templates'),
    loader=FileSystemLoader('foolfuuka/templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

def thread_html(board_name:str, thread_id:int):
    template = env.get_template('thread.html')
    
    # use the existing json hug function to grab the data
    thread_dict = convert(board_name, thread_id)
    
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
