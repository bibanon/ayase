#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import html
import yaml
import time
import pymysql.cursors

SELECT_POST = "SELECT * FROM `{}` WHERE `num`={}"
SELECT_POST_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{}` WHERE `num`={})"
SELECT_THREAD = "SELECT * FROM `{}` WHERE `thread_num`={} ORDER BY `num`"
SELECT_THREAD_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{}` WHERE `thread_num`={})"
SELECT_THREAD_DETAILS = "SELECT `nreplies`, `nimages` FROM `{}_threads` WHERE `thread_num`={}"
SELECT_THREAD_OP = "SELECT * FROM `{}` WHERE `thread_num`={} AND op=1"
SELECT_THREAD_OP_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{}` WHERE `thread_num`={} AND op=1)"
SELECT_THREAD_PREVIEW = "SELECT * FROM `{}` WHERE `thread_num`={} ORDER BY `num` DESC LIMIT 5"
SELECT_THREAD_PREVIEW_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{}` WHERE `thread_num`={} ORDER BY `num`)" #ERROR 1235 (42000): This version of MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
SELECT_THREAD_LIST_BY_OFFSET = "SELECT `thread_num` FROM `{}_threads` ORDER BY `time_last` DESC LIMIT 10 OFFSET {}"


CONF = {}
connection = ''

def load_config():
    with open("config.yml", 'r') as yaml_conf:
        global CONF 
        CONF = yaml.safe_load(yaml_conf)

def create_connection():
    load_config()
    global connection
    connection = pymysql.connect(host=CONF['mysql']['host'],
                             port=CONF['mysql']['port'],
                             user=CONF['mysql']['user'],
                             password=CONF['mysql']['password'],
                             db=CONF['mysql']['db'],
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

def check_connection():
    global connection
    if(connection.open):
        return True
    create_connection()
    return False


def get_post(board:str, post_num:int):
    sql = SELECT_POST.format(board, post_num)
    return db_handler(sql, fetchall=False)

def get_post_images(board:str, post_num:int):
    sql = SELECT_POST_IMAGES.format(board, board, post_num)
    return db_handler(sql, fetchall=False)

def get_thread(board:str, thread_num:int):
    sql = SELECT_THREAD.format(board, thread_num)
    return db_handler(sql, fetchall=True)

def get_thread_images(board:str, thread_num:int):
    sql = SELECT_THREAD_IMAGES.format(board, board, thread_num)
    return db_handler(sql, fetchall=True)

def get_thread_details(board:str, thread_num:int):
    sql = SELECT_THREAD_DETAILS.format(board, thread_num)
    return db_handler(sql, fetchall=False)

def get_thread_op(board:str, thread_num:int):
    sql = SELECT_THREAD_OP.format(board, thread_num)
    return db_handler(sql, fetchall=False)

def get_thread_op_images(board:str, thread_num:int):
    sql = SELECT_THREAD_OP_IMAGES.format(board, board, thread_num)
    return db_handler(sql, fetchall=False)

def get_thread_preview(board:str, thread_num:int):
    sql = SELECT_THREAD_PREVIEW.format(board, thread_num)
    return db_handler(sql, fetchall=True)
    
def get_thread_preview_images(board:str, thread_num:int):
    sql = SELECT_THREAD_PREVIEW_IMAGES.format(board, board, thread_num)
    return db_handler(sql, fetchall=True)

def get_thread_list(board:str, page_num:int):
    sql = SELECT_THREAD_LIST_BY_OFFSET.format(board, page_num * 10)
    return db_handler(sql, fetchall=True)

    
def db_handler(sql:str, fetchall:bool):
    try:
        connection.ping(reconnect=True)
        with connection.cursor() as cursor:
            cursor.execute(sql)
            if(fetchall):
                return cursor.fetchall()
            else:
                return cursor.fetchone()
    except:
        print("Query failed!")
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
            split_by_line[i] = """<span class="quote">%s</span>"""  % curr_line
        elif "&gt;&gt;" in curr_line: #TODO: handle situations where text is in front or after the redirect 
            subsplit_by_space = curr_line.split(" ")
            for j in range(len(subsplit_by_space)):
                curr_word = subsplit_by_space[j]
                # handle >>(post-num)
                if(curr_word[:8] == "&gt;&gt;" and curr_word[8:].isdigit()):
                    quotelink_list.append(curr_word[8:])
                    subsplit_by_space[j] = """<a href="#p%s" class="quotelink">%s</a>""" % (curr_word[8:], curr_word)
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
        #TODO: implement [code] tags on /g/
        if "[code]" in curr_line:
            if "[/code]" in curr_line:
                split_by_line[i] = """<code>""".join(split_by_line[i].split("[code]"))
                split_by_line[i] = """</code>""".join(split_by_line[i].split("[/code]"))
            else:
                split_by_line[i] = """<pre>""".join(split_by_line[i].split("[code]"))
        elif "[/code]" in curr_line:
            split_by_line[i] = """</pre>""".join(split_by_line[i].split("[/code]"))
        if "[banned]" in curr_line:
            split_by_line[i] = """<span class="banned">""".join(split_by_line[i].split("[banned]"))
            split_by_line[i] = "</span>".join(split_by_line[i].split("[/banned]"))
    return quotelink_list, "</br>".join(split_by_line)

#
# Generate a board index.
#
def generate_index(board_name:str, page_num:int, html=True):
    page_num -= 1
    thread_list = get_thread_list(board_name, page_num)
    
    #for each thread, get the first 5 posts and put them in 'threads'
    threads = []
    for i in range(len(thread_list)):
        thread_id = thread_list[i]['thread_num']
        try:
            thread_op, op_quotelinks = convert_thread_op(board_name, thread_id)
        except TypeError as e:
            print(e)
            print("Thread", thread_id, "is empty! Skipping it.", file=sys.stderr)
            raise(e)
            continue
        
        asagi_thread, quotelinks = convert_thread_preview(board_name, thread_id)
        details = get_thread_details(board_name, thread_id)
        
        combined = {}
        
        #determine number of omitted posts
        omitted_posts = details['nreplies'] - len(asagi_thread['posts']) - 1 #subtract OP 
        thread_op['posts'][0]['omitted_posts'] = omitted_posts
        
        #determine number of omitted images
        num_images_shown = 0
        for i in range(len(asagi_thread['posts'])):
            post = asagi_thread['posts'][i]
            if(post['md5'] and post['resto'] != 0):
                num_images_shown += 1
            # add quotelinks to thread
            if(html):
                asagi_thread['posts'][i]['quotelinks'] = quotelinks

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

#
# Generate a single post
#
def convert_post(board_name:str, post_id:int):
    post = [get_post(board_name, post_id)]
    images = [get_post_images(board_name, post_id)]
    return convert(post, images=images, isPost=True)

#
# Generate the OP post
#
def convert_thread_op(board_name:str, thread_id:int):
    op_post = [get_thread_op(board_name, thread_id)]
    images = [get_thread_op_images(board_name, thread_id)]
    details = get_thread_details(board_name, thread_id)
    return convert(op_post, details, images)

#
# Generate a thread preview, removing OP post
#
def convert_thread_preview(board_name:str, thread_id:int):
    thread = get_thread_preview(board_name, thread_id)
    images = get_thread_preview_images(board_name, thread_id)
    for i in range(len(thread)):
        if(thread[i]['op'] == 1):
            del thread[i]
            
    thread.reverse()
    return convert(thread, images=images)

#
# Convert threads to 4chan api
#
def convert_thread(board_name:str, thread_id:int):
    thread = get_thread(board_name, thread_id)
    images = get_thread_images(board_name, thread_id)
    details = get_thread_details(board_name, thread_id)
    return convert(thread, details, images)
    
#
# Converts asagi API data to 4chan API format. 
#
def convert(thread, details=None, images=None, isPost=False):
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
        if(len(images) > 0):
            #filter(lambda person: person['name'] == 'Pam', people)
            #find dict where media_hash is equal
            try:
                for media in filter(lambda image: image['media_hash'] == thread[i]['media_hash'], images):
                    if(media['preview_reply'] is None and media['media']):
                        posts[i]['asagi_preview_filename'] = media['media'].split('.')[0] + "s.jpg"
                    posts[i]['asagi_preview_filename'] = media['preview_reply']
                    posts[i]['asagi_filename'] = media['media']
            except TypeError:
                pass
        else:
            posts[i]['asagi_preview_filename'] = thread[i]['preview_orig']
            posts[i]['asagi_filename'] = thread[i]['media_orig']
        if(thread[i]['media_filename'] is not None and thread[i]['media_filename'] is not False):
            posts[i]['filename'] = thread[i]['media_filename'].split('.')[0]
            posts[i]['ext'] = "." + thread[i]['media_filename'].split('.')[1]
        posts[i]['w'] = thread[i]['media_w']
        posts[i]['h'] = thread[i]['media_h']
        posts[i]['tn_w'] = thread[i]['preview_w']
        posts[i]['tn_h'] = thread[i]['preview_h']
        try:
            if thread[i]['media_orig'] is None:
                posts[i]['tim'] = (thread[i]['timestamp'] * 1000)  #temporarily add 3 digits to fit microtime
            else:
                posts[i]['tim'] = int(thread[i]['media_orig'].split('.')[0]) 
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
        posts[i]['country'] = thread[i]['poster_country']
        posts[i]['closed'] = thread[i]['locked']
        posts[i]['filedeleted'] = thread[i]['deleted']
        posts[i]['exif'] = thread[i]['exif']
        
        # generate comment content
        post_quotelinks, posts[i]['com'] = restore_comment(thread[i]['comment'], thread[i]['num'])
        for quotelink in post_quotelinks: # for each quotelink in the post, 
            if(quotelink not in quotelink_map):
                quotelink_map[quotelink] = []
            quotelink_map[quotelink].append(posts[i]['no']) # add the current post.no to the quotelink's post.no key
    if(isPost):
        return posts[0]
    
    #print(quotelink_map, file=sys.stderr)
    result['posts'] = posts
    return result, quotelink_map

create_connection()
