#!/usr/bin/python3
# -*- coding: utf-8 -*-

import httpx
import json
from datetime import datetime

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse

from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel

# TODO: standardize database and configuration loading across asagi.py and future implementation of ayase.py to one db loader file
from view.asagi import app, debug, CONF

#add session middleware to support cookies
app.add_middleware(SessionMiddleware, secret_key=CONF['session_secret'], max_age=CONF['oauth2']['cookie_expiration'])

#create api subgroup
admin = FastAPI(openapi_prefix="/admin")

class InvalidCookieException(Exception):
    def __init__(self, message):
        super().__init__(message)

#
# Request dependency, verifies if a cookie is expired
#
async def verify_date(request:Request):
    print(request.session)
    if request.session and datetime.now().timestamp() > request.session['exp']:
        raise InvalidCookieException("Cookie is expired")
    if not request.session:
        return False
    return True

# import moderation tools after shared variables and functions are initialized
import model.moderation

@admin.exception_handler(InvalidCookieException)
async def invalid_cookie_handler(request: Request, e:InvalidCookieException):
    return RedirectResponse(url='/admin/login')

@admin.get("/", response_class=HTMLResponse, include_in_schema=False)
async def admin_index(request:Request):
    if(request.session):
        return RedirectResponse(url='/')
    return RedirectResponse(url='/admin/login')

@admin.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login(request:Request):
    # handle none-type authentication
    # TODO: in the future, different authentication backends should be
    # completely separated and placed in separate files to be loaded by the authentication_type config option
    if(CONF['authentication_type'] == 'none'):
        request.session.update({
            "user": 'none', 
            "group": 'none',
            "iat": int(datetime.now().timestamp()),
            "exp": int(datetime.now().timestamp()) + 86400
        })
        return RedirectResponse(url='/')
    return f"""<a href="{CONF['oauth2']['login_url']}?client_id={CONF['oauth2']['client_id']}&redirect_uri={CONF['site_url']}/admin/token/&response_type=code&state=login&scope=openid">click here to login with gitgud</a>"""

@admin.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    return None

@admin.get("/token/", include_in_schema=False, dependencies=[Depends(verify_date)])
async def read_token(code:str, request:Request, state:str = None):
    data = {"client_id": CONF['oauth2']['client_id'], "client_secret": CONF['oauth2']['secret'], "code": code, "grant_type": "authorization_code", "redirect_uri": CONF['site_url'] + "/admin/token/"}
    
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{CONF['oauth2']['token_url']}", data=data)
        try:
            access_token = json.loads(r.text)['access_token']
        except:
            raise HTTPException(
                status_code=403, detail="Failed to get access token."
            )
        r = await client.get(f"{CONF['oauth2']['userinfo_url']}", params={"access_token": access_token})
        try:
            response = json.loads(r.text)
            groups = response['groups']
            for group in groups:
                if(group in CONF['oauth2']['groups'].values()):
                    request.session.update({
                        "user": response['nickname'], 
                        "group": group,
                        "iat": int(datetime.now().timestamp()),
                        "exp": int(datetime.now().timestamp()) + CONF['oauth2']['cookie_expiration'] 
                    })
                    return RedirectResponse(url='/')
                
            raise HTTPException(
                status_code=403, detail="Not Authorized"
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=403, detail="Failed authentication."
            )

@admin.get("/verify_session/", include_in_schema=False, dependencies=[Depends(verify_date)])
async def verify_session(request:Request):
    return {"session": request.session}
    
app.mount("/admin", admin)

