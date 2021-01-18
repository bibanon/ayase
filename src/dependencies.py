from fastapi import Request
from datetime import datetime
from src.core.settings import config


class InvalidCookieException(Exception):
    def __init__(self, message):
        super().__init__(message)


#
# Request dependency, verifies if a cookie is expired
#
async def check_token(request: Request):
    print(request.session)
    if request.session and datetime.now().timestamp() > request.session['exp']:
        raise InvalidCookieException("Cookie is expired")
    if not request.session:
        return False
    return True


async def check_admin_cookies(request: Request):
    if(config['options']['reports']):
        return await check_token(request)
    return False


def get_skin(request: Request):
    try:
        skin_cookie = request.cookies.get("ayase_skin")
        return skin_cookie if skin_cookie else config["default_skin"]
    except:
        return config["default_skin"]


