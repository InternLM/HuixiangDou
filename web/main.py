import uvicorn

from web.util.log import log
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web.api.access import api
from web.config.logging import LOGGING_CONFIG

# log
logger = log(__name__)

# define global variable
API_VER = 'v1'

# FastAPI setting
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router=api, prefix=f"/{API_VER}/access")


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
        port=23333,
        timeout_keep_alive=600,
        workers=3,
        log_config= LOGGING_CONFIG
    )


if __name__ == "__main__":
    main()
