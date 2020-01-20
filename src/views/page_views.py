import datetime

import aiohttp_jinja2
from aiohttp import web

# from .auth import AuthMixin
from .base_view import BaseView


class Pages(BaseView):

    @classmethod
    async def top_100_page(cls, request):
        context = {
            'date': cls.yesterday,
            'routes': request.app.router,
        }
        q_date = request.match_info.get('date')
        if q_date:
            context['date'] = datetime.datetime.strptime(q_date, '%Y-%m-%d')
        response = aiohttp_jinja2.render_template('top100.html.j2', request, context)
        return response

    @classmethod
    async def customer_report_page(cls, request):
        context = {
            'date': cls.yesterday,
            'routes': request.app.router,
        }
        q_date = request.match_info.get('date')
        if q_date:
            context['date'] = datetime.datetime.strptime(q_date, '%Y-%m-%d')
        context['customer_name'] = request.match_info.get('customer_name')
        response = aiohttp_jinja2.render_template('customer_report.html.j2', request,
                                                  context=context)
        return response
