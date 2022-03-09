import logging
import html
from src.core.database import DB
from src.core.settings import config

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
    (CASE WHEN `media_orig` IS NULL THEN timestamp * 1000
        ELSE SUBSTRING_INDEX(media_orig, '.', 1) END) AS `tim`,
    `{board}`.`media_hash` AS `md5`,
    `media_size` AS `fsize`,
    (CASE WHEN `media_filename` IS NULL THEN NULL
        ELSE SUBSTRING_INDEX(media_filename, '.', 1) END) AS `filename`,
    (CASE WHEN `media_filename` IS NULL THEN NULL
        ELSE SUBSTRING_INDEX(media_filename, '.', -1) END) AS `ext`,
    (CASE WHEN op=1 THEN CAST(0 AS UNSIGNED)
        ELSE `{board}`.`thread_num` END) AS `resto`,
    (CASE WHEN capcode='N' THEN NULL ELSE `capcode` END) AS `capcode`,
    `trip`,
    `spoiler`,
    `poster_country` AS `country`,
    `{board}`.`locked` AS `closed`,
    `deleted` AS `filedeleted`,
    `exif`,
    `comment` AS `com` """

MD5_IMAGE_SELECTOR = "`media_hash`,`media`,`preview_reply`,`preview_op`"
SHA256_IMAGE_SELECTOR = "`media_hash`,LOWER(HEX(`media_sha256`)) AS `media_sha256`,LOWER(HEX(`preview_reply_sha256`)) AS `preview_reply_sha256`,LOWER(HEX(`preview_op_sha256`)) AS `preview_op_sha256`"


async def query_handler(sql: str, fetchall: bool):
    return await DB.getInstance().query_handler(sql, fetchall)


async def get_post(board: str, post_num: int):
    SELECT_POST = SELECTOR + "FROM `{board}` WHERE `num`={post_num}"
    sql = SELECT_POST.format(board=board, post_num=post_num)
    return await query_handler(sql, fetchall=False)


async def get_post_images(board: str, post_num: int):
    SELECT_POST_IMAGES = "SELECT {image_selector} FROM `{board}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{board}` WHERE `num`={post_num})"
    sql = SELECT_POST_IMAGES.format(
        board=board,
        post_num=post_num,
        image_selector=SHA256_IMAGE_SELECTOR if "hash_format" in config and config["hash_format"] == "sha256" else MD5_IMAGE_SELECTOR
    )
    return await query_handler(sql, fetchall=False)


async def get_thread(board: str, thread_num: int):
    SELECT_THREAD = SELECTOR + "FROM `{board}` WHERE `thread_num`={thread_num} ORDER BY `num`"
    sql = SELECT_THREAD.format(board=board, thread_num=thread_num)
    return await query_handler(sql, fetchall=True)


async def get_thread_images(board: str, thread_num: int):
    SELECT_THREAD_IMAGES = "SELECT {image_selector} FROM `{board}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{board}` WHERE `thread_num`={thread_num})"
    sql = SELECT_THREAD_IMAGES.format(
        board=board,
        thread_num=thread_num,
        image_selector=SHA256_IMAGE_SELECTOR if "hash_format" in config and config["hash_format"] == "sha256" else MD5_IMAGE_SELECTOR
    )
    return await query_handler(sql, fetchall=True)


async def get_thread_details(board: str, thread_num: int):
    SELECT_THREAD_DETAILS = "SELECT `nreplies`, `nimages` FROM `{board}_threads` WHERE `thread_num`={thread_num}"
    sql = SELECT_THREAD_DETAILS.format(board=board, thread_num=thread_num)
    return await query_handler(sql, fetchall=False)


async def get_thread_preview(board: str, thread_num: int):
    SELECT_THREAD_PREVIEW = SELECTOR + "FROM `{board}` WHERE `thread_num`={thread_num} ORDER BY `num` DESC LIMIT 5" 
    sql = SELECT_THREAD_PREVIEW.format(board=board, thread_num=thread_num)
    return await query_handler(sql, fetchall=True)


async def get_thread_preview_images(board: str, thread_num: int):
    SELECT_THREAD_PREVIEW_IMAGES = "SELECT {image_selector} FROM `{board}_images` WHERE `media_hash` IN (SELECT `media_hash` FROM `{board}` WHERE `thread_num`={thread_num} ORDER BY `num`)"  
    sql = SELECT_THREAD_PREVIEW_IMAGES.format(
        board=board,
        thread_num=thread_num,
        image_selector=SHA256_IMAGE_SELECTOR if "hash_format" in config and config["hash_format"] == "sha256" else MD5_IMAGE_SELECTOR    
    )
    return await query_handler(sql, fetchall=True)


async def get_op_list(board: str, page_num: int):
    SELECT_OP_LIST_BY_OFFSET = SELECTOR + "FROM {board} INNER JOIN {board}_threads ON {board}_threads.thread_num = {board}.thread_num WHERE OP=1 ORDER BY `time_bump` DESC LIMIT 10 OFFSET {page_num};"
    sql = SELECT_OP_LIST_BY_OFFSET.format(board=board, page_num=page_num * 10)
    return await query_handler(sql, fetchall=True)


async def get_op_images(board: str, md5s: list):
    SELECT_OP_IMAGE_LIST_BY_MEDIA_HASH = "SELECT {image_selector} FROM `{board}_images` WHERE `media_hash` IN {md5s}"
    sql = SELECT_OP_IMAGE_LIST_BY_MEDIA_HASH.format(
        board=board,
        md5s=md5s,
        image_selector=SHA256_IMAGE_SELECTOR if "hash_format" in config and config["hash_format"] == "sha256" else MD5_IMAGE_SELECTOR
    )
    return await query_handler(sql, fetchall=True)


async def get_op_details(board: str, thread_nums: list):
    SELECT_OP_DETAILS_LIST_BY_THREAD_NUM = "SELECT `nreplies`, `nimages` FROM `{board}_threads` WHERE `thread_num` IN {thread_nums} ORDER BY FIELD(`thread_num`, {field_thread_nums})"
    field_thread_nums = str(thread_nums)[1:-1]
    sql = SELECT_OP_DETAILS_LIST_BY_THREAD_NUM.format(
        board=board,
        thread_nums=thread_nums,
        field_thread_nums=field_thread_nums
    )
    return await query_handler(sql, fetchall=True)


async def get_gallery_threads(board: str, page_num: int):
    SELECT_GALLERY_THREADS_BY_OFFSET = SELECTOR + "FROM `{board}` INNER JOIN `{board}_threads` ON `{board}`.`thread_num` = `{board}_threads`.`thread_num` WHERE OP=1 ORDER BY `{board}_threads`.`time_bump` DESC LIMIT 150 OFFSET {page_num};"
    sql = SELECT_GALLERY_THREADS_BY_OFFSET.format(board=board, page_num=page_num * 150)
    return await query_handler(sql, fetchall=True)


async def get_gallery_images(board: str, page_num: int):
    SELECT_GALLERY_THREAD_IMAGES_MD5 = "SELECT `{board}`.media_hash, `{board}_images`.`media`, `{board}_images`.`preview_reply`, `{board}_images`.`preview_op` FROM ((`{board}` INNER JOIN `{board}_threads` ON `{board}`.`thread_num` = `{board}_threads`.`thread_num`) INNER JOIN `{board}_images` ON `{board}_images`.`media_hash` = `{board}`.`media_hash`) WHERE OP=1 ORDER BY `{board}_threads`.`time_bump` DESC LIMIT 150 OFFSET {page_num};"
    SELECT_GALLERY_THREAD_IMAGES_SHA256 = "SELECT `{board}`.media_hash, LOWER(HEX(`{board}_images`.`media_sha256`)) AS `media_sha256`, LOWER(HEX(`{board}_images`.`preview_reply_sha256`)) AS `preview_reply_sha256`, LOWER(HEX(`{board}_images`.`preview_op_sha256`)) AS `preview_op_sha256` FROM ((`{board}` INNER JOIN `{board}_threads` ON `{board}`.`thread_num` = `{board}_threads`.`thread_num`) INNER JOIN `{board}_images` ON `{board}_images`.`media_hash` = `{board}`.`media_hash`) WHERE OP=1 ORDER BY `{board}_threads`.`time_bump` DESC LIMIT 150 OFFSET {page_num};" 
    selector = SELECT_GALLERY_THREAD_IMAGES_SHA256 if "hash_format" in config and config["hash_format"] == "sha256" else SELECT_GALLERY_THREAD_IMAGES_MD5
    sql = selector.format(board=board, page_num=page_num)
    return await query_handler(sql, fetchall=True)


async def get_gallery_details(board: str, page_num: int):
    SELECT_GALLERY_THREAD_DETAILS = "SELECT `nreplies`, `nimages` FROM `{board}_threads` ORDER BY `time_bump` DESC LIMIT 150 OFFSET {page_num}"
    sql = SELECT_GALLERY_THREAD_DETAILS.format(board=board, page_num=page_num)
    return await query_handler(sql, fetchall=True)


#
# Re-convert asagi stripped comment into clean html
# Also create a dictionary with keys containing the post.no, which maps to a
# tuple containing the posts it links to.
# Returns a String (the processed comment) and a list (list of quotelinks in
# the post).
#
def restore_comment(com: str, post_no: int):
    try:
        com_line = html.escape(com).split("\n")  # split by line
    except AttributeError:
        if com is not None:
            raise ()
        return "", ""
    quotelink_list = []
    # greentext definition: a line that begins with a single ">" and ends with
    # a '\n'
    # redirect definition: a line that begins with a single ">>", has a thread
    # number afterward that exists in the current thread or another thread
    # (may be inline)
    # >> (show OP)
    # >>>/g/ (board redirect)
    # >>>/g/<post_num> (board post redirect)
    for i in range(len(com_line)):
        curr_line = com_line[i]
        if "&gt;" == curr_line[:4] and "&gt;" != curr_line[4:8]:
            com_line[i] = f"""<span class="quote">{curr_line}</span>"""
            continue
        elif (
            "&gt;&gt;" in curr_line
        ):  # TODO: handle situations where text is in front or after the
            # redirect
            subsplit_by_space = curr_line.split(" ")
            for j in range(len(subsplit_by_space)):
                curr_word = subsplit_by_space[j]
                # handle >>(post-num)
                if curr_word[:8] == "&gt;&gt;" and curr_word[8:].isdigit():
                    quotelink_list.append(curr_word[8:])
                    subsplit_by_space[j] = (
                        f"""<a href="#p{curr_word[8:]}" class="quotelink">{curr_word}</a>"""
                    )
                # TODO: build functionality
            com_line[i] = " ".join(subsplit_by_space)
        if "[" in curr_line and "]" in curr_line:
            com_line[i] = """<span class="spoiler">""".join(
                com_line[i].split("[spoiler]")
            )
            com_line[i] = "</span>".join(com_line[i].split("[/spoiler]"))
            com_line[i] = "</span>".join(com_line[i].split("[/spoiler]"))
            if "[code]" in curr_line:
                if "[/code]" in curr_line:
                    com_line[i] = """<code>""".join(com_line[i].split("[code]"))
                    com_line[i] = """</code>""".join(com_line[i].split("[/code]"))
                else:
                    com_line[i] = """<pre>""".join(com_line[i].split("[code]"))
            com_line[i] = """</pre>""".join(com_line[i].split("[/code]"))
            com_line[i] = """<span class="banned">""".join(com_line[i].split("[banned]"))
            com_line[i] = "</span>".join(com_line[i].split("[/banned]"))
    return quotelink_list, "</br>".join(com_line)


#
# Generate a board index.
#
async def generate_index(board_name: str, page_num: int, html=True):
    page_num -= 1  # start from 0 when running queries
    op_list = await convert_thread_ops(board_name, page_num)
    # for each thread, get the first 5 posts and put them in 'threads'
    threads = []
    for op in op_list:
        thread_id = op["posts"][0]["no"]
        asagi_thread, quotelinks = await convert_thread_preview(
            board_name, thread_id
        )

        # determine number of omitted posts
        omitted_posts = (
            op["posts"][0]["replies"] - len(asagi_thread["posts"]) - 1
        )  # subtract OP
        op["posts"][0]["omitted_posts"] = omitted_posts

        # determine number of omitted images
        num_images_shown = 0
        for i in range(len(asagi_thread["posts"])):
            post = asagi_thread["posts"][i]
            if post["md5"] and post["resto"] != 0:
                num_images_shown += 1
            # add quotelinks to thread
            if html:
                asagi_thread["posts"][i]["quotelinks"] = quotelinks

        omitted_images = op["posts"][0]["images"] - num_images_shown
        if op["posts"][0]["md5"]:
            omitted_images -= 1  # subtract OP if OP has image

        op["posts"][0]["omitted_images"] = omitted_images

        combined = {}
        # if the thread has only one post, don't repeat OP post.
        if op["posts"][0]["replies"] == 0:
            combined = op
        else:
            combined["posts"] = op["posts"] + asagi_thread["posts"]

        threads.append(combined)

    # encapsulate threads around a dict
    result = {}
    result["threads"] = threads

    return result


#
# Generate gallery structure
#
async def generate_gallery(board_name: str, page_num: int):
    page_num -= 1  # start page number at 1
    thread_list = await get_gallery_threads(board_name, page_num)
    details = await get_gallery_details(board_name, page_num)
    images = await get_gallery_images(board_name, page_num)

    gallery_list = convert(thread_list, details, images, isGallery=True)

    result = []
    page_threads = {"page": 0, "threads": []}
    for i in range(len(thread_list)):
        # new page every 15 threads
        if i % 15 == 0 and i != 0:
            result.append(page_threads)
            page_threads = {"page": (i // 14) + 1, "threads": []}
        page_threads["threads"].append(gallery_list[i])
    # add the last page threads
    result.append(page_threads)
    return result


#
# Generate a single post
#
async def convert_post(board_name: str, post_id: int):
    post = [await get_post(board_name, post_id)]
    images = [await get_post_images(board_name, post_id)]
    return convert(post, images=images, isPost=True)


#
# Generate the OP post
#
async def convert_thread_ops(board_name: str, page_num: int):
    op_list = await get_op_list(board_name, page_num)
    op_image_list = await get_op_images(
        board_name, tuple([op.md5 for op in op_list])
    )
    op_detail_list = await get_op_details(
        board_name, tuple([op.no for op in op_list])
    )
    return convert(op_list, op_detail_list, op_image_list, isOPs=True)


#
# Generate a thread preview, removing OP post
#
async def convert_thread_preview(board_name: str, thread_id: int):
    thread = await get_thread_preview(board_name, thread_id)
    images = await get_thread_preview_images(board_name, thread_id)
    for i in range(len(thread)):
        if thread[i]["resto"] == 0:
            del thread[i]

    thread.reverse()
    return convert(thread, images=images)


#
# Convert threads to 4chan api
#
async def convert_thread(board_name: str, thread_id: int):
    thread = await get_thread(board_name, thread_id)
    images = await get_thread_images(board_name, thread_id)
    details = [
        await get_thread_details(board_name, thread_id)
    ]  # details needs to be an array
    return convert(thread, details, images)


#
# Converts asagi API data to 4chan API format.
#
def convert(
        thread,
        details=None,
        images=None,
        isOPs=False,
        isPost=False,
        isGallery=False
):
    result = {}
    quotelink_map = {}
    posts = []
    for i in range(len(thread)):
        if not thread or not thread[i]:
            continue

        # The record object doesn't support assignment so we convert it to a
        # normal dict
        posts.append(dict(thread[i]))

        # TODO: asagi records time using an incorrect timezone configuration
        # which will need to be corrected
        if images and len(images) > 0:
            # find dict where media_hash is equal
            try:
                for media in filter(
                    lambda image: (image["media_hash"] == posts[i]["md5"])
                    if image
                    else False,
                    images,
                ):
                    if("hash_format" in config and config["hash_format"] == "sha256"):
                        if(posts[i]["resto"] == 0):
                            if media["preview_op_sha256"] is not None:
                                posts[i]["asagi_preview_filename"] = f'{media["preview_op_sha256"]}.jpg'
                            else:
                                logging.warning(f"{posts[i]['no']} OP thumbnail missing.")
                        else:
                            if media["preview_reply_sha256"] is not None:
                                posts[i]["asagi_preview_filename"] = f'{media["preview_reply_sha256"]}.{posts[i]["ext"]}'
                            else:
                                logging.warning(f"{posts[i]['no']} post thumbnail missing.")
                        if(media["media_sha256"] is not None):
                            posts[i]["asagi_filename"] = f'{media["media_sha256"]}.{posts[i]["ext"]}'
                        else:
                            logging.warning(f"{posts[i]['no']} media filename missing.")
                    else:
                        # use preview_op for op images
                        if(posts[i]["resto"] == 0):
                            posts[i]["asagi_preview_filename"] = media["preview_op"]
                        else:
                            posts[i]["asagi_preview_filename"] = media["preview_reply"]
                        posts[i]["asagi_filename"] = media["media"]
            except Exception as e:
                logging.error(f"{e}")

        # leaving semantic_url empty for now
        if details and posts[i]["resto"] == 0:
            posts[i]["replies"] = details[i]["nreplies"]
            posts[i]["images"] = details[i]["nimages"]

        # generate comment content
        if not isGallery:
            post_quotelinks, posts[i]["com"] = restore_comment(
                posts[i]["com"], posts[i]["no"]
            )
            for quotelink in post_quotelinks:  # for each quotelink in the post
                if quotelink not in quotelink_map:
                    quotelink_map[quotelink] = []
                quotelink_map[quotelink].append(
                    posts[i]["no"]
                )  # add the current post.no to the quotelink's post.no key

    if isPost:
        return posts[0] if len(posts) > 0 else posts

    if isGallery:
        return posts

    if isOPs:
        result = []
        for op in posts:
            result.append({"posts": [op]})
        return result

    result["posts"] = posts
    return result, quotelink_map
