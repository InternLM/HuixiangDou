#!/usr/bin/env python3
# This is the main entrance of Huixiangdou-WEB.
# This project is written under python 3.9

import os

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

import web.api.access as access
import web.api.qalib as qalib
import web.api.statistic as statistic
from web.api import chat, integrate, message
from web.config.env import HuixiangDouEnv
from web.config.logging import LOGGING_CONFIG
from web.middleware.token import check_hxd_token
from web.scheduler.huixiangdou_task import start_scheduler, stop_scheduler
from web.util.log import log
from web.util.str import safe_join

# log
logger = log(__name__)

# define global variable
API_VER = 'v1'
SERVER_PORT = HuixiangDouEnv.get_server_port()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_RESOURCE_DIR = os.path.join(BASE_DIR, 'front-end', 'dist')
ASSETS_RESOURCE_DIR = os.path.join(STATIC_RESOURCE_DIR, 'assets')

# FastAPI setting
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router=access.access_api, prefix=f'/api/{API_VER}/access')
app.include_router(router=qalib.qalib_api,
                   prefix=f'/api/{API_VER}/qalib',
                   dependencies=[Depends(check_hxd_token)])
app.include_router(router=integrate.integrate_api,
                   prefix=f'/api/{API_VER}/qalib',
                   dependencies=[Depends(check_hxd_token)])
app.include_router(router=statistic.statistic_api,
                   prefix=f'/api/{API_VER}/statistic')
app.include_router(router=chat.chat_api,
                   prefix=f'/api/{API_VER}/chat',
                   dependencies=[Depends(check_hxd_token)])
app.include_router(router=message.message_api,
                   prefix=f'/api/{API_VER}/message')


@app.get('/', response_class=HTMLResponse)
@app.get('/home', response_class=HTMLResponse)
@app.get('/bean-detail/', response_class=HTMLResponse)
async def server():
    return FileResponse(f'{STATIC_RESOURCE_DIR}/index.html')


@app.get('/assets/{path:path}')
async def resource_assets(path: str):
    return FileResponse(safe_join(ASSETS_RESOURCE_DIR, path))


@app.get('/{path:path}')
async def resource_other(path: str):
    return FileResponse(safe_join(STATIC_RESOURCE_DIR, path))


@app.on_event('startup')
def on_startup():
    start_scheduler()


@app.on_event('shutdown')
def on_shutdown():
    stop_scheduler()


@app.exception_handler(HTTPException)
async def global_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


def main():
    """main function start server use uvicorn default workers: 3 default port:

    23333.
    """
    HuixiangDouEnv.print_env()
    uvicorn.run('web.main:app',
                host='0.0.0.0',
                port=int(SERVER_PORT),
                timeout_keep_alive=600,
                workers=3,
                log_config=LOGGING_CONFIG)


if __name__ == '__main__':
    main()
