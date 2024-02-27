from typing import List

from fastapi import APIRouter, Response, Request, UploadFile, File, Depends

from web.middleware.token import check_hxd_token
from web.model.qalib import QalibPositiveNegative, QalibInfo
from web.service.qalib import QaLibService

qalib_api = APIRouter()


@qalib_api.post("/v1/getInfo")
async def qalib_info(request: Request, response: Response, hxd_info: QalibInfo = Depends(check_hxd_token)):
    return await QaLibService(request, response, hxd_info).info()


@qalib_api.post("/v1/addDocs")
async def qalib_add_docs(request: Request, response: Response, files: List[UploadFile] = File(...),
                         hxd_info: QalibInfo = Depends(check_hxd_token)):
    return await QaLibService(request, response, hxd_info).add_docs(files)


@qalib_api.post("/v1/getSampleInfo")
async def qalib_get_sample_info(request: Request, response: Response, hxd_info: QalibInfo = Depends(check_hxd_token)):
    return await QaLibService(request, response, hxd_info).get_sample_info()


@qalib_api.post("/v1/updateSampleInfo")
async def qalib_update_sample_info(request: Request, response: Response, body: QalibPositiveNegative,
                                   hxd_info: QalibInfo = Depends(check_hxd_token)):
    return await QaLibService(request, response, hxd_info).update_sample_info(body)
