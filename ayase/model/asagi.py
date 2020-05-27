#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import html
import time
import pymysql.cursors

SELECT_THREAD = "SELECT * FROM `{}` WHERE `thread_num`={} ORDER BY `num`"
SELECT_THREAD_DETAILS = "SELECT `nreplies`, `nimages` FROM `{}_threads` WHERE `thread_num`={}"
SELECT_THREAD_OP = "SELECT * FROM `{}` WHERE `thread_num`={} AND op=1"
SELECT_THREAD_PREVIEW = "SELECT * FROM `{}` WHERE `thread_num`={} ORDER BY `num` DESC LIMIT 5"
SELECT_THREAD_LIST_BY_OFFSET = "SELECT `thread_num` FROM `{}_threads` ORDER BY `thread_num` DESC LIMIT 10 OFFSET {}"

connection = pymysql.connect(host='192.168.2.52',
                             user='root',
                             password='jetfuelcantmeltsteelbeams',
                             db='4ch',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

def get_thread(board:str, thread_num:int):
    try:
        with connection.cursor() as cursor:
            sql = SELECT_THREAD.format(board, thread_num)
            cursor.execute(sql)
            return cursor.fetchall()
    except:
        print("Failed to get thread!")
        return ''

def get_thread_details(board:str, thread_num:int):
    try:
        with connection.cursor() as cursor:
            sql = SELECT_THREAD_DETAILS.format(board, thread_num)
            cursor.execute(sql)
            return cursor.fetchone()
    except:
        print("Failed to get thread details!")
        return ''

def get_thread_op(board:str, thread_num:int):
    try:
        with connection.cursor() as cursor:
            sql = SELECT_THREAD_OP.format(board, thread_num)
            cursor.execute(sql)
            return cursor.fetchone()
    except:
        print("Failed to get OP post!")
        return ''

def get_thread_preview(board:str, thread_num:int):
    try:
        with connection.cursor() as cursor:
            sql = SELECT_THREAD_PREVIEW.format(board, thread_num)
            cursor.execute(sql)
            return cursor.fetchall()
    except:
        print("Failed to get thread!")
        return ''

def get_thread_list(board:str, page_num:int):
    try:
        with connection.cursor() as cursor:
            sql = SELECT_THREAD_LIST_BY_OFFSET.format(board, page_num * 10)
            cursor.execute(sql)
            return cursor.fetchall()
    except:
        print("Failed to get thread list!")
        return ''
    
#
# Re-convert asagi stripped comment into clean html
# Also create a dictionary with keys containing the post.no, which maps to a tuple containing the posts it links to. 
# Returns a String (the processed comment) and a list (list of quotelinks in the post).
#
def restore_comment(com:str, post_no:int):
    try:
        split_by_line = html.escape(com).split("\n")
    except AttributeError:
        if com != None:
            raise()
        return '', ''
    quotelink_list = []
    #greentext definition: a line that begins with a single ">" and ends with a '\n'
    #redirect definition: a line that begins with a single ">>", has a thread number afterward that exists in the current thread or another thread (may be inline)
    # >> (show OP)
    # >>>/g/ (board redirect)
    # >>>/g/<post_num> (board post redirect)
    for i in range(len(split_by_line)):
        curr_line = split_by_line[i]
        if "&gt;" == curr_line[:4] and "&gt;" != curr_line[4:8]:
            split_by_line[i] = """<span class="greentext">%s</span>"""  % curr_line
        elif "&gt;&gt;" in curr_line: #TODO: handle situations where text is in front or after the redirect 
            subsplit_by_space = curr_line.split(" ")
            for j in range(len(subsplit_by_space)):
                curr_word = subsplit_by_space[j]
                # handle >>(post-num)
                if(curr_word[:8] == "&gt;&gt;" and curr_word[8:].isdigit()):
                    quotelink_list.append(curr_word[8:])
                    subsplit_by_space[j] = """<a class="quotelink" href="#p%s" data-function="highlight" data-backlink="true" data-board="" data-post="%s">%s</a>""" % (curr_word[8:], curr_word[8:], curr_word)
                # handle >>>/<board-name>/
                #elif(curr_word[:12] == "&gt;&gt;&gt;" and '/' in curr_word[14:]):
                    ##TODO: build functionality
                    #print("board redirect not yet implemented!: " + curr_word, file=sys.stderr)
            split_by_line[i] = ' '.join(subsplit_by_space)
        if "[spoiler]" in curr_line:
            split_by_line[i] = """<span class="spoiler">""".join(split_by_line[i].split("[spoiler]"))
            split_by_line[i] = "</span>".join(split_by_line[i].split("[/spoiler]"))
        elif "[/spoiler]" in curr_line:
            split_by_line[i] = "</span>".join(split_by_line[i].split("[/spoiler]"))
    return quotelink_list, "</br>".join(split_by_line)

def generate_index(board_name:str, page_num:int):
    page_num -= 1
    thread_list = get_thread_list(board_name, page_num)
    
    #for each thread, get the first 5 posts and put them in 'threads'
    threads = []
    for i in range(len(thread_list)):
        thread_id = thread_list[i]['thread_num']
        thread_op, temp = convert_thread_op(board_name, thread_id)

        asagi_thread, temp = convert_thread_preview(board_name, thread_id)
        details = get_thread_details(board_name, thread_id)
        
        combined = {}
        
        #determine number of omitted posts
        omitted_posts = details['nreplies'] - len(asagi_thread['posts']) - 1 #subtract OP 
        thread_op['posts'][0]['omitted_posts'] = omitted_posts
        
        #determine number of omitted images
        num_images_shown = 0
        for post in asagi_thread['posts']:
            if(post['md5'] and post['resto'] != 0):
                num_images_shown += 1
        omitted_images = details['nimages'] - num_images_shown 
        if thread_op['posts'][0]['md5']:
            omitted_images -= 1 #subtract OP if OP has image
        
        thread_op['posts'][0]['omitted_images'] = omitted_images

        # if the thread has only one post, don't repeat OP post.
        if(thread_op['posts']==asagi_thread['posts']):
            combined = thread_op
        else:
            combined['posts'] = thread_op['posts'] + asagi_thread['posts']

        threads.append(combined)
    
    #encapsulate threads around a dict
    result = {}
    result['threads'] = threads
    
    return result
    
def convert_thread_op(board_name:str, thread_id:int):
    op_post = [get_thread_op(board_name, thread_id)]
    details = get_thread_details(board_name, thread_id)
    return convert(op_post, details)

def convert_thread_preview(board_name:str, thread_id:int):
    thread = get_thread_preview(board_name, thread_id)
    for i in range(len(thread)):
        if(thread[i]['op'] == 1):
            del thread[i]
            
    thread.reverse()
    return convert(thread)

# Convert to 4chan api
def convert_thread(board_name:str, thread_id:int):
    thread = get_thread(board_name, thread_id)
    details = get_thread_details(board_name, thread_id)
    return convert(thread, details)
    
def convert(thread, details=None):
    result = {}
    quotelink_map = {}
    posts = []
    for i in range(len(thread)):
        posts.append({})
        posts[i]['no'] = thread[i]['num']
        posts[i]['sticky'] = thread[i]['sticky']
        posts[i]['closed'] = 1
        #TODO: asagi records time using an incorrect timezone configuration which will need to be corrected 
        posts[i]['now'] = time.strftime('%m/%d/%y(%a)%H:%M:%S', time.localtime(thread[i]['timestamp'])) #convert timestamp to properly formatted time
        posts[i]['name'] = thread[i]['name']
        posts[i]['sub'] = thread[i]['title'] if thread[i]['title'] != None else ''        
        posts[i]['asagi_filename'] = thread[i]['media_orig']
        if(thread[i]['media_filename'] is not None and thread[i]['media_filename'] is not False):
            posts[i]['filename'] = thread[i]['media_filename'].split('.')[0]
            posts[i]['ext'] = "." + thread[i]['media_filename'].split('.')[1]
        posts[i]['w'] = thread[i]['media_w']
        posts[i]['h'] = thread[i]['media_h']
        posts[i]['tn_w'] = thread[i]['preview_w']
        posts[i]['tn_h'] = thread[i]['preview_h']
        try:
            posts[i]['tim'] = thread[i]['timestamp'] * 1000 if thread[i]['media_orig'] is None else int(thread[i]['media_orig'].split('.')[0]) #temporarily add 3 digits to fit microtime
        except ValueError:
            print(thread[i]['media_orig'])
        posts[i]['time'] = thread[i]['timestamp']
        posts[i]['md5'] = thread[i]['media_hash']
        posts[i]['fsize'] = thread[i]['media_size']
        posts[i]['op'] = thread[i]['op'] # adds op even though not specified in 4chan api
        if(thread[i]['op'] == 1):
            posts[i]['resto'] = 0
        else:
            posts[i]['resto'] = thread[i]['thread_num']
        
        if(thread[i]['capcode'] == "N"):
            posts[i]['capcode'] = None
        else:
            posts[i]['capcode'] = thread[i]['capcode']
        # leaving semantic_url empty for now
        if(details):
            posts[i]['replies'] = details['nreplies']
            posts[i]['images'] = details['nimages']
        posts[i]['trip'] = thread[i]['trip']
        posts[i]['spoiler'] = thread[i]['spoiler']
        posts[i]['country_name'] = thread[i]['poster_country']
        posts[i]['closed'] = thread[i]['locked']
        posts[i]['filedeleted'] = thread[i]['deleted']
        
        # generate comment content
        post_quotelinks, posts[i]['com'] = restore_comment(thread[i]['comment'], thread[i]['num'])
        for quotelink in post_quotelinks: # for each quotelink in the post, 
            if(quotelink not in quotelink_map):
                quotelink_map[quotelink] = []
            quotelink_map[quotelink].append(posts[i]['no']) # add the current post.no to the quotelink's post.no key
    
    #print(quotelink_map, file=sys.stderr)
    result['posts'] = posts
    return result, quotelink_map
