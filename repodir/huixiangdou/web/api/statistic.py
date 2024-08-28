from fastapi import APIRouter, Request, Response

from web.service.statistic import StatisticService

statistic_api = APIRouter()


@statistic_api.get('/v1/total')
async def qalib_info_statistic(request: Request, response: Response):
    return await StatisticService(request, response).info_statistic()
