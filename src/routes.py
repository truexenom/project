from aiohttp import web

# from views.auth import AuthView
from views.customer_api import CustomerView
from views.page_views import Pages
from views.report_api import ReportView


routes = [
    # Page views
    web.get('/', Pages.top_100_page, name='root'),
    web.get('/{date:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))}',
            Pages.top_100_page, name='top_100_by_date_page'),
    web.get('/{date:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))}/{customer_name}',
            Pages.customer_report_page, name='customer_page'),
    # Report views
    web.get(
        '/date/{q_date:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))}/customer/{customer_name}/report',
        ReportView.report_data, name='report_data'),
    web.get('/date/{date:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))}',
            ReportView.top_100, name='top_100_data'),
    # Customer data
    web.get(
        '/date/{q_date:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))}/customer/{customer_name}',
        CustomerView.customer_data, name='customer_data'),
    # Auth
    # web.get('/login', AuthView.login, name='login'),
    # web.get('/auth', AuthView.google_auth_redirect, name='auth'),
    # web.get('/logout', AuthView.logout, name='logout'),
]
