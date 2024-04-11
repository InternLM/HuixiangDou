from fastapi import APIRouter, Depends, Request, Response

from web.middleware.token import check_hxd_token
from web.model.integrate import IntegrateLarkBody, IntegrateWebSearchBody
from web.model.qalib import QalibInfo
from web.service.qalib import QaLibService

integrate_api = APIRouter()


@integrate_api.post('/v1/integrateLark')
async def integrate_lark(request: Request,
                         response: Response,
                         body: IntegrateLarkBody,
                         hxd_info: QalibInfo = Depends(check_hxd_token)):
    return await QaLibService(request, response, hxd_info).integrate_lark(body)


@integrate_api.post('/v1/integrateWebSearch')
async def integrate_web_search(request: Request,
                               response: Response,
                               body: IntegrateWebSearchBody,
                               hxd_info: QalibInfo = Depends(check_hxd_token)):
    return await QaLibService(request, response,
                              hxd_info).integrate_web_search(body)
