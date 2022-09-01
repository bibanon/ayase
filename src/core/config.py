
from typing import List

from pydantic import AnyHttpUrl, BaseSettings, BaseModel, validator


class Board(BaseModel):
    shortname: str
    name: str


class Skins(BaseModel):
    slug: str
    name: str


class Schema(BaseModel):
    name: str = "asagi"


class Options(BaseModel):
    post_selector: bool = true
    stats: bool = false
    ghost: bool = false
    search: bool = false
    reports: bool = false


class ImageLocation(BaseModel):
    image: str = "/img/{board_name}/image"
    thumb: str = "/img/{board_name}/thumb"


class OAuth2Groups(BaseModel):
    admins: str = "gitgud-admin-group"
    moderators: str = "gitgud-mod-group"


class OAuth2(BaseModel):
    provider: str = "gitgud"
    login_url: str = "https://gitgud.io/oauth/authorize"
    token_url: str = "https://gitgud.io/oauth/token"
    userinfo_url: str = "https://gitgud.io/oauth/userinfo"
    client_id: str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    secret: str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    cookie_expiration: int = 86400 
    oauth2 = {"groups": OAuth2Groups()}

class MySQL(BaseModel):
    host: str
    port: int
    db: str
    user: str
    password: str
    charset: str



class Settings(BaseSettings):
    site_name: str = "Ayase"
    hash_format: str
    debug: bool
    session_secret: str
    archives: List[Board] = list()
    boards: List[Board] = list()
    skins: List[Skins] = list()
    schema: Schema = Schema()
    options: Options = Options()
    image_location: ImageLocation = ImageLocation()
    

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
