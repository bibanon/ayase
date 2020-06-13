#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import html
import json
import time
import pymysql.cursors
import timeit

SELECTOR = """SELECT
    `num` AS `no`, 
    (CASE WHEN 1=1 THEN 1 ELSE NULL END) AS `closed`, 
    DATE_FORMAT(FROM_UNIXTIME(`timestamp`), "%m/%d/%y(%a)%H:%i:%S") AS `now`, 
    `name`,
    `{board}`.`sticky`,
    (CASE WHEN `title` IS NULL THEN '' ELSE `title` END) AS `sub`,
    `media_w` AS `w`,
    `media_h` AS `h`,
    `preview_w` AS `tn_w`,
    `preview_h` AS `tn_h`,
    `timestamp` AS `time`,
    `preview_orig` AS `asagi_preview_filename`,
    `media_orig` AS `asagi_filename`,
    (CASE WHEN `media_orig` IS NULL THEN timestamp * 1000 ELSE SUBSTRING_INDEX(media_orig, '.', 1) END) AS `tim`,
    `{board}`.`media_hash` AS `md5`, 
    `media_size` AS `fsize`, 
    SUBSTRING_INDEX(media_filename, '.', 1) AS `filename`,
    SUBSTRING_INDEX(media_filename, '.', -1) AS `ext`,
    (CASE WHEN op=1 THEN CAST(0 AS UNSIGNED) ELSE `{board}`.`thread_num` END) AS `resto`, 
    (CASE WHEN capcode='N' THEN NULL ELSE `capcode` END) AS `capcode`,
    `trip`,
    `spoiler`,
    `poster_country` AS `country`,
    `{board}`.`locked` AS `closed`, 
    `deleted` AS `filedeleted`, 
    `exif`, 
    `comment` AS `com` """
    #(SELECT `media` FROM {board}_images WHERE {board}.media_hash={board}_images.media_hash) AS asagi_filename,
    #(CASE WHEN (SELECT `preview_reply` FROM {board}_images WHERE {board}.media_hash={board}_images.media_hash) IS NULL THEN CONCAT(SUBSTRING_INDEX((SELECT `media` FROM {board}_images WHERE {board}.media_hash={board}_images.media_hash), '.', 1), 's.jpg') ELSE (SELECT `preview_reply` FROM {board}_images WHERE {board}.media_hash={board}_images.media_hash) END) AS asagi_preview_filename,

SELECT_POST = SELECTOR + "FROM `{board}` WHERE `num`={post_num}"
SELECT_POST_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{board}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{board}` WHERE `num`={post_num})"
SELECT_THREAD = SELECTOR + "FROM `{board}` WHERE `thread_num`={thread_num} ORDER BY `num`"
SELECT_THREAD_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{board}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{board}` WHERE `thread_num`={thread_num})"
SELECT_THREAD_DETAILS = "SELECT `nreplies`, `nimages` FROM `{board}_threads` WHERE `thread_num`={thread_num}"
SELECT_THREAD_OP = SELECTOR + "FROM `{board}` WHERE `thread_num`={thread_num} AND op=1"
SELECT_THREAD_OP_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{board}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{board}` WHERE `thread_num`={thread_num} AND op=1)"
SELECT_THREAD_PREVIEW = SELECTOR + "FROM `{board}` WHERE `thread_num`={thread_num} ORDER BY `num` DESC LIMIT 5"
SELECT_THREAD_PREVIEW_IMAGES = "SELECT `media_hash`,`media`,`preview_reply` FROM `{board}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{board}` WHERE `thread_num`={thread_num} ORDER BY `num`)" #ERROR 1235 (42000): This version of MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
SELECT_THREAD_LIST_BY_OFFSET = "SELECT `thread_num` FROM `{board}_threads` ORDER BY `time_last` DESC LIMIT 10 OFFSET {page_num}"
SELECT_GALLERY_THREADS_BY_OFFSET = SELECTOR + "FROM `{board}` INNER JOIN `{board}_threads` ON `{board}`.`thread_num` = `{board}_threads`.`thread_num` WHERE OP=1 ORDER BY `{board}_threads`.`time_last` DESC LIMIT 150 OFFSET {page_num};"
SELECT_GALLERY_THREAD_IMAGES = "SELECT `{board}`.media_hash, `{board}_images`.`media`, `{board}_images`.`preview_reply` FROM ((`{board}` INNER JOIN `{board}_threads` ON `{board}`.`thread_num` = `{board}_threads`.`thread_num`) INNER JOIN `{board}_images` ON `{board}_images`.`media_hash` = `{board}`.`media_hash`) WHERE OP=1 ORDER BY `{board}_threads`.`time_last` DESC LIMIT 150 OFFSET {page_num};"
SELECT_GALLERY_THREAD_DETAILS = "SELECT `nreplies`, `nimages` FROM `{board}_threads` ORDER BY `time_last` DESC LIMIT 150 OFFSET {page_num}"

CONF = {}
connection = ''

def load_config():
    with open("config.json", 'r') as json_conf:
        global CONF 
        CONF = json.load(json_conf)

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
    sql = SELECT_POST.format(board=board, post_num=post_num)
    return db_handler(sql, fetchall=False)

def get_post_images(board:str, post_num:int):
    sql = SELECT_POST_IMAGES.format(board=board, post_num=post_num)
    return db_handler(sql, fetchall=False)

def get_thread(board:str, thread_num:int):
    sql = SELECT_THREAD.format(board=board, thread_num=thread_num)
    return db_handler(sql, fetchall=True)

def get_thread_images(board:str, thread_num:int):
    sql = SELECT_THREAD_IMAGES.format(board=board, thread_num=thread_num)
    return db_handler(sql, fetchall=True)

def get_thread_details(board:str, thread_num:int):
    sql = SELECT_THREAD_DETAILS.format(board=board, thread_num=thread_num)
    return db_handler(sql, fetchall=False)

def get_thread_op(board:str, thread_num:int):
    sql = SELECT_THREAD_OP.format(board=board, thread_num=thread_num)
    return db_handler(sql, fetchall=False)

def get_thread_op_images(board:str, thread_num:int):
    sql = SELECT_THREAD_OP_IMAGES.format(board=board, thread_num=thread_num)
    return db_handler(sql, fetchall=False)

def get_thread_preview(board:str, thread_num:int):
    sql = SELECT_THREAD_PREVIEW.format(board=board, thread_num=thread_num)
    return db_handler(sql, fetchall=True)
    
def get_thread_preview_images(board:str, thread_num:int):
    sql = SELECT_THREAD_PREVIEW_IMAGES.format(board=board, thread_num=thread_num)
    return db_handler(sql, fetchall=True)

def get_thread_list(board:str, page_num:int):
    sql = SELECT_THREAD_LIST_BY_OFFSET.format(board=board, page_num=page_num * 10)
    return db_handler(sql, fetchall=True)

def get_gallery_threads(board:str, page_num:int):
    sql = SELECT_GALLERY_THREADS_BY_OFFSET.format(board=board, page_num=page_num * 150)
    return db_handler(sql, fetchall=True)

def get_gallery_images(board:str, page_num:int):
    sql = SELECT_GALLERY_THREAD_IMAGES.format(board=board, page_num=page_num)
    return db_handler(sql, fetchall=True)

def get_gallery_details(board:str, page_num:int):
    sql = SELECT_GALLERY_THREAD_DETAILS.format(board=board, page_num=page_num)
    return db_handler(sql,fetchall=True)
    
def db_handler(sql:str, fetchall:bool):
    try:
        connection.ping(reconnect=True)
        with connection.cursor() as cursor:
            start = timeit.default_timer()
            cursor.execute(sql)
            if(fetchall):
                result = cursor.fetchall()
                end = timeit.default_timer()
                print('Time waiting for query: ', end-start)
                return result
            else:
                result = cursor.fetchone()
                end = timeit.default_timer()
                print('Time waiting for query: ', end-start)
                return result
    except Exception as e:
        print(e)
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
        #if "[code]" in curr_line:
            #if "[/code]" in curr_line:
                #split_by_line[i] = """<code>""".join(split_by_line[i].split("[code]"))
                #split_by_line[i] = """</code>""".join(split_by_line[i].split("[/code]"))
            #else:
                #split_by_line[i] = """<pre>""".join(split_by_line[i].split("[code]"))
        #elif "[/code]" in curr_line:
            #split_by_line[i] = """</pre>""".join(split_by_line[i].split("[/code]"))
        #if "[banned]" in curr_line:
            #split_by_line[i] = """<span class="banned">""".join(split_by_line[i].split("[banned]"))
            #split_by_line[i] = "</span>".join(split_by_line[i].split("[/banned]"))
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
        except TypeError:
            print("Thread", thread_id, "is empty! Skipping it.", file=sys.stderr)
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
# Generate gallery structure
#
def generate_gallery(board_name:str, page_num:int):
    page_num -= 1 #start page number at 1
    thread_list = get_gallery_threads(board_name, page_num)
    details = get_gallery_details(board_name, page_num)
    
    gallery_list = convert(thread_list, details, isGallery=True)
    
    result = []
    page_threads = {'page': 0, 'threads': []}
    for i in range(len(thread_list)):
        #new page every 15 threads
        if(i % 15 == 0 and i != 0):
            result.append(page_threads)
            page_threads = {'page': (i//14)+1, 'threads': []}
        
        page_threads['threads'].append(gallery_list[i])
    #add the last page threads
    result.append(page_threads)
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
    details = [get_thread_details(board_name, thread_id)] #details needs to be an array
    return convert(op_post, details, images)

#
# Generate a thread preview, removing OP post
#
def convert_thread_preview(board_name:str, thread_id:int):
    thread = get_thread_preview(board_name, thread_id)
    images = get_thread_preview_images(board_name, thread_id)
    for i in range(len(thread)):
        if(thread[i]['resto'] == 0):
            del thread[i]
            
    thread.reverse()
    return convert(thread, images=images)

#
# Convert threads to 4chan api
#
def convert_thread(board_name:str, thread_id:int):
    thread = get_thread(board_name, thread_id)
    images = get_thread_images(board_name, thread_id)
    details = [get_thread_details(board_name, thread_id)]
    return convert(thread, details, images)
    
#
# Converts asagi API data to 4chan API format. 
#
def convert(thread, details=None, images=None, isPost=False, isGallery=False):
    result = {}
    quotelink_map = {}
    for i in range(len(thread)):
        #TODO: asagi records time using an incorrect timezone configuration which will need to be corrected 
        if(images and len(images) > 0):
            ##find dict where media_hash is equal
            try:
                for media in filter(lambda image: image['media_hash'] == thread[i]['md5'], images):
                    if(media['preview_reply'] is None and media['media']):
                        thread[i]['asagi_preview_filename'] = media['media'].split('.')[0] + "s.jpg"
                    thread[i]['asagi_preview_filename'] = media['preview_reply']
                    thread[i]['asagi_filename'] = media['media']
            except TypeError:
                pass

        #else:
            #thread[i]['asagi_preview_filename'] = thread[i]['preview_orig']
            #thread[i]['asagi_filename'] = thread[i]['media_orig']
        
        # leaving semantic_url empty for now
        if(details and thread[i]['resto'] == 0):
            thread[i]['replies'] = details[i]['nreplies']
            thread[i]['images'] = details[i]['nimages']
        
        # generate comment content
        if(not isGallery):
            post_quotelinks, thread[i]['com'] = restore_comment(thread[i]['com'], thread[i]['no'])
            for quotelink in post_quotelinks: # for each quotelink in the post, 
                if(quotelink not in quotelink_map):
                    quotelink_map[quotelink] = []
                quotelink_map[quotelink].append(thread[i]['no']) # add the current post.no to the quotelink's post.no key
            
    if(isPost):
        return thread[0]
    
    if(isGallery):
        return thread
    
    #print(quotelink_map, file=sys.stderr)
    result['posts'] = thread
    return result, quotelink_map

create_connection()
