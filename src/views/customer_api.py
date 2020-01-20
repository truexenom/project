from aiohttp import web

from views.base_view import BaseView
from data_puller import CustomerData


class CustomerView(BaseView):
    @classmethod
    async def customer_data(cls, request):
        has_access = False
        if is_logged:
            user_info = await cls.get_user_info(request)
            has_access = await cls.is_in_group(user_info['email'],
                                               cls.config['permissions']['common'])
        if not all([is_logged, has_access]):
            return web.HTTPForbidden()
        async with CustomerData(cls.mongo_client) as gatherer:
            customer_data = await gatherer.get_current_date_data(**request.match_info)
        response = web.json_response(customer_data, dumps=cls.dumper)
        return response
