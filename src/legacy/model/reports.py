#!/usr/bin/python3
# -*- coding: utf-8 -*-

import yaml
import databases
import datetime
from pydantic import BaseModel
from fastapi import Request
# TODO: standardize database and configuration loading across asagi.py and future implementation of ayase.py to one db loader file
from view.asagi import app, debug, CONF, DB_ENGINE 

SELECT_RULES = "SELECT * FROM rules"
SELECT_REPORTS = "SELECT `id`,`board`,`no`,`rule_id`,`reason`,INET_NTOA(`ip_reporter`) AS `ip_reporter`,`created` FROM reports"
SELECT_REPORTS_BY_BOARD = "SELECT `id`,`board`,`no`,`rule_id`,`reason`,INET_NTOA(`ip_reporter`) AS `ip_reporter`,`created` FROM reports WHERE board = :board"
INSERT_REPORTS = "INSERT INTO reports(board, no, rule_id, reason, ip_reporter, created) VALUES (:board, :no, :rule_id, :reason, INET_ATON(:ip_reporter), :created)"
DELETE_REPORTS = "DELETE FROM reports WHERE id = :id"

global database
database = None
DATABASE_URL = "{engine}://{user}:{password}@{host}:{port}/{database}"

@app.on_event("startup")
async def startup():
    global database
    url = DATABASE_URL.format(
        engine=DB_ENGINE,
        host=CONF["reports_db"][DB_ENGINE]["host"],
        port=CONF["reports_db"][DB_ENGINE]["port"],
        user=CONF["reports_db"][DB_ENGINE]["user"],
        password=CONF["reports_db"][DB_ENGINE]["password"],
        database=CONF["reports_db"][DB_ENGINE]["db"],
    )
    database = databases.Database(url)
    await database.connect()
    
@app.on_event("shutdown")
async def shutdown():
    if database:
        await database.disconnect()
        
async def select_handler(sql: str, values, fetchall: bool):
    try:
        #if not debug:
        return (
            (await database.fetch_all(query=sql, values=values))
            if fetchall
            else (await database.fetch_one(query=sql, values=values))
        )
    except Exception as e:
        print(f"Query failed!: {e}")
        return ""

async def execute_handler(sql: str, values, execute_many: bool):
    try:
        #if not debug:
        return (
            (await database.execute_many(query=sql, values=values))
            if execute_many
            else (await database.execute(query=sql, values=values))
        )
    except Exception as e:
        print(f"Query failed!: {e}")
        return ""
    
class Report(BaseModel):
    no:int
    rule_id:int
    reason:str = None
    
class BulkReport(BaseModel):
    reason:str
    rule_id:int
    posts:list

@app.get("/rules.json")
async def get_rules():
    sql = SELECT_RULES
    values = {}
    return await select_handler(sql, values, fetchall=True)

@app.get("/reports.json")
async def get_reports():
    sql = SELECT_REPORTS
    values = {}
    return await select_handler(sql, values, fetchall=True)

@app.get("/{board_name}/reports.json")
async def get_reports_by_board(board_name: str):
    sql = SELECT_REPORTS_BY_BOARD
    values = {"board": board_name}
    return await select_handler(sql, values, fetchall=True)

@app.post("/{board_name}/reports")
async def insert_report(board_name: str, report: Report, request: Request):
    sql = INSERT_REPORTS
    values = {
        "board": board_name, 
        "no": report.no,  
        "rule_id": report.rule_id, 
        "reason": report.reason, 
        "ip_reporter": request.client.host,
        "created": datetime.datetime.utcnow()
        }
    return await execute_handler(sql, values, execute_many=False)

@app.post("/reports/bulk")
async def insert_bulk_reports(reports: BulkReport, request: Request):
    sql = INSERT_REPORTS
    for post in reports.posts:
        values = {
            "board": post['board'], 
            "no": post['no'],  
            "rule_id": reports.rule_id, 
            "reason": reports.reason, 
            "ip_reporter": request.client.host,
            "created": datetime.datetime.utcnow()
            }
        await execute_handler(sql, values, execute_many=False)

@app.delete("/{board_name}/reports/{report_id}")
async def delete_reports_by_board(board_name:str, report_id:int):
    sql = DELETE_REPORTS
    values = {"board": board_name, "id": report_id}
    return await execute_handler(sql, values, execute_many=False)

@app.delete("/reports/{report_id}")
async def delete_reports(report_id:int):
    sql = DELETE_REPORTS
    values = {"id": report_id}
    return await execute_handler(sql, values, execute_many=False)

