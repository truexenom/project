from aiohttp import web

from data_puller import CustomerData
from views.base_view import BaseView

# from .auth import AuthMixin


class ReportView(BaseView):

    @classmethod
    async def top_100(cls, request):
        async with CustomerData(cls.mongo_client) as gatherer:
            data = await gatherer.get_top_100(request.match_info.get('date'))
        response = web.json_response(data)
        return response

    @classmethod
    async def report_data(cls, request):
        async with CustomerData(cls.mongo_client) as gatherer:
            customer_data = await gatherer.get_report_data(**request.match_info)
        response = web.json_response(customer_data, dumps=cls.dumper)
        return response
