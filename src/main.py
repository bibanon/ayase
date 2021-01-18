from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
import subprocess
from .routers import template, api
from src.core.database import init_db, shutdown_db


def custom_openapi(openapi_prefix: str):
    if app.openapi_schema:
        return app.openapi_schema
    revision = "0.1.0"
    try:
        revision = (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                stdout=subprocess.PIPE,
            )
            .stdout.decode("utf-8")
            .rstrip()
        )
    except Exception:
        pass
    openapi_schema = get_openapi(
        title="Ayase",
        version=revision,
        description="The Ayase Imageboard Archival Standard",
        routes=app.routes,
        openapi_prefix=openapi_prefix,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://c4.wallpaperflare.com/wallpaper/530/77/135/anime-yotsuba-fuuka-ayase-mr-koiwai-yotsuba-wallpaper-preview.jpg"
        # "url": "https://c4.wallpaperflare.com/wallpaper/487/5/317/anime-yotsuba-fuuka-ayase-wallpaper-preview.jpg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


template_name = "foolfuuka"

app = FastAPI()

# Routers
app.include_router(template.router)
app.include_router(api.router)

# Mount staic files
app.mount(
    "/static",
    StaticFiles(directory=f"templates/{template_name}/static"),
    name="static"
)

app.openapi = custom_openapi


# Prepare DB
@app.on_event("startup")
async def startup():
    init_db()


@app.on_event("shutdown")
async def shutdown():
    shutdown_db()
