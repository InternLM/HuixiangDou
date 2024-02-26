import uvicorn
from starlette.responses import HTMLResponse
from fastapi.responses import FileResponse

from web.util.log import log
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import web.api.access as access
import web.api.qalib as qalib
import web.api.statistic as statistic
from web.config.logging import LOGGING_CONFIG
from web.scheduler.huixiangdou_task import start_scheduler, stop_scheduler
from web.util.str import safe_join
import os


# log
logger = log(__name__)

# define global variable
API_VER = 'v1'
SERVER_PORT = os.getenv("SERVER_PORT") if os.getenv("SERVER_PORT") else "23333"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_RESOURCE_DIR = os.path.join(BASE_DIR, "front-end", "dist")
ASSETS_RESOURCE_DIR = os.path.join(STATIC_RESOURCE_DIR, "assets")

# FastAPI setting
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router=access.access_api, prefix=f"/api/{API_VER}/access")
app.include_router(router=qalib.qalib_api, prefix=f"/api/{API_VER}/qalib")
app.include_router(router=statistic.statistic_api, prefix=f"/api/{API_VER}/statistic")


@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
async def server():
    return FileResponse(f"{STATIC_RESOURCE_DIR}/index.html")


@app.get("/assets/{path:path}")
async def resource_assets(path: str):
    return FileResponse(safe_join(ASSETS_RESOURCE_DIR, path))


@app.get("/{path:path}")
async def resource_other(path: str):
    return FileResponse(safe_join(STATIC_RESOURCE_DIR, path))


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


def main():
    """
    main function
    start server use uvicorn
    default workers: 3
    default port: 23333
    """
    uvicorn.run(
        "web.main:app",
        host='0.0.0.0',
        port=int(SERVER_PORT),
        timeout_keep_alive=600,
        workers=3,
        log_config=LOGGING_CONFIG
    )


if __name__ == "__main__":
    main()
