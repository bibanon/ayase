#!/usr/bin/python3
# -*- coding: utf-8 -*-

import httpx
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from ..dependencies import check_token
from src.core.settings import config

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def admin_index(request: Request):
    if(request.session):
        return RedirectResponse(url='/')
    return RedirectResponse(url='/admin/login')


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login(request: Request):
    # handle none-type authentication
    # TODO: in the future, different authentication backends should be
    # completely separated and placed in separate files to be loaded by the
    # authentication_type config option
    if(config['authentication_type'] == 'none'):
        request.session.update({
            "user": 'none',
            "group": 'none',
            "iat": int(datetime.now().timestamp()),
            "exp": int(datetime.now().timestamp()) + 86400
        })
        return RedirectResponse(url='/')
    return f"""<a href="{config['oauth2']['login_url']}?client_id={config['oauth2']['client_id']}&redirect_uri={config['site_url']}/admin/token/&response_type=code&state=login&scope=openid">click here to login with gitgud</a>"""


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    return None


@router.get(
    "/token/",
    include_in_schema=False,
    dependencies=[Depends(check_token)]
)
async def read_token(
    code: str,
    request: Request,
    state: str = None
):
    data = {
        "client_id": config['oauth2']['client_id'],
        "client_secret": config['oauth2']['secret'],
        "code": code, "grant_type": "authorization_code",
        "redirect_uri": config['site_url'] + "/admin/token/"
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{config['oauth2']['token_url']}", data=data)
        try:
            access_token = json.loads(r.text)['access_token']
        except ValueError:
            raise HTTPException(
                status_code=403, detail="Failed to get access token."
            )
        r = await client.get(
            f"{config['oauth2']['userinfo_url']}",
            params={"access_token": access_token}
        )
        try:
            response = json.loads(r.text)
            groups = response['groups']
            for group in groups:
                if(group in config['oauth2']['groups'].values()):
                    request.session.update({
                        "user": response['nickname'],
                        "group": group,
                        "iat": int(datetime.now().timestamp()),
                        "exp": int(datetime.now().timestamp()) + config['oauth2']['cookie_expiration']
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


@router.get(
    "/verify_session/",
    include_in_schema=False,
    dependencies=[Depends(check_token)]
)
async def verify_session(request: Request):
    return {"session": request.session}
