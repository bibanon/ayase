#!/usr/bin/python3
# -*- coding: utf-8 -*-

from fastapi import Depends
from fastapi.responses import JSONResponse

# TODO: standardize database and configuration loading across asagi.py and future implementation of ayase.py to one db loader file
from view.asagi import archive_list, board_list
from model.asagi import database
from view.moderation import admin, check_token

COLUMN_LIST = "doc_id, media_id, poster_ip, num, subnum, thread_num, op, timestamp, timestamp_expired, preview_orig, preview_w, preview_h, media_filename, media_w, media_h, media_size, media_hash, media_orig, spoiler, deleted, capcode, email, name, trip, title, comment, delpass, sticky, locked, poster_hash, poster_country, exif"
INSERT_THREAD_INTO_DELETED="INSERT INTO {board}_deleted SELECT * FROM {board} WHERE thread_num=:thread_num;"
DELETE_THREAD = "DELETE FROM {board} WHERE thread_num=:thread_num;"
INSERT_POST_INTO_DELETED = "INSERT INTO {board}_deleted SELECT * FROM {board} WHERE num=:num;"
DELETE_POST = "DELETE FROM {board} WHERE num=:num;"

async def execute_handler(sql, values, execute_many: bool):
    from model.asagi import database
    transaction = await database.transaction()
    try:
        #if not debug:
        if execute_many:
            await database.execute_many(query=sql, values=values)
        else:
            await database.execute(query=sql, values=values)
    except Exception as e:
        await transaction.rollback()
        print(f"Query failed!: {e}")
        print(sql)
        raise
    else:
        await transaction.commit()

@admin.delete("/{board}/thread/{thread_num}", include_in_schema=False, dependencies=[Depends(check_token)])
async def delete_thread(board:str, thread_num:int):
    if board in archive_list or board in board_list:
        try:
            await execute_handler((INSERT_THREAD_INTO_DELETED + DELETE_THREAD).format(board=board), {"thread_num": thread_num}, False)
            return JSONResponse (
                content={'status': 'success'}
            )
        except Exception as e:
            return JSONResponse (
                status_code=500,
                content={'status': 'failed', 'msg': 'could not delete, sql query failed.', 'err': f'{e}'}
            )
    return JSONResponse (
        status_code=404,
        content={'status': 'failed', 'msg': 'no such board'}
    )
@admin.delete("/{board}/post/{num}", include_in_schema=False, dependencies=[Depends(check_token)])
async def delete_post(board:str, num:int):
    if board in archive_list or board in board_list:
        try:
            await execute_handler((INSERT_POST_INTO_DELETED + DELETE_POST).format(board=board), {"num": num}, False)
            return JSONResponse (
                content={'status': 'success'}
            )
        except Exception as e:
            return JSONResponse (
                status_code=500,
                content={'status': 'failed', 'msg': 'could not delete, sql query failed.', 'err': f'{e}'}
            )
    return JSONResponse (
        status_code=404,
        content={'status': 'failed', 'msg': 'no such board'}
    )
