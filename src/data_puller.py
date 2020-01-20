import asyncio
import datetime
import inspect
import json
import logging
from inspect import signature
import calendar

import aiomysql
import motor.motor_asyncio
import pymongo
from bson import json_util


def cache(cls, method):

    @wraps(method)
    def wrapper(self):
        sig = signature(method)
        if sig not in self._cache.keys():
            self._cache[sig] = method(self)
        return self._cache[method.__name__]

    return wrapper


class CustomerData:
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=2)

    logger = logging.getLogger('CustomerData')

    _cache = {}

    def __init__(self, mongo_client):
        self.mongo_client = mongo_client
        self.mongo_db = self.mongo_client['customer_report']
        self.report_collection = self.mongo_db['customer_data']

    async def __aenter__(self):
        await self.report_collection.create_index([
            ('date', pymongo.DESCENDING),
            ('customer_name', pymongo.DESCENDING),
        ])
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get_top_100(self, q_date):
        q_date_obj = datetime.datetime.strptime(q_date, '%Y-%m-%d')
        next_date = q_date_obj + datetime.timedelta(days=1)
        filt = {'date': {'$gte': q_date_obj, '$lt': next_date}}
        projection = {'customer_name': True, '_id': False}
        cursor = self.report_collection.find(filt, projection).sort(
            'daily_traffic', pymongo.DESCENDING).limit(100)
        top_100 = [i['customer_name'] for i in await cursor.to_list(None)]
        return {'date': q_date, 'customers': top_100}

    async def get_current_date_data(self, customer_name, q_date):
        q_date_obj = datetime.datetime.strptime(q_date, '%Y-%m-%d')
        next_date = q_date_obj + datetime.timedelta(days=1)
        filt = {
            'date': {
                '$gte': q_date_obj,
                '$lt': next_date
            },
            'customer_name': customer_name
        }
        projection = {'_id': False}
        return await self.report_collection.find_one(filt, projection)

    def _last_day_of_month(self, q_date):
        if q_date.month == 12:
            return q_date.replace(day=31)
        return q_date.replace(month=q_date.month+1, day=1) - datetime.timedelta(days=1)

    async def get_month_summary(self, customer_name, first_day, last_day):
        pipeline = [
            {
            '$match': {'$and': [{'date': {'$gte': first_day}},
                                {'date': {'$lte': last_day}},
                                {'customer_name': customer_name}]}
            },
            {
            '$group': {'_id': False, 'summary': {'$sum': '$daily_traffic'}}
            }
        ]
        results = await self.report_collection.aggregate(pipeline).to_list(10000)
        result = results[0] if results else {}
        return result.get('summary', 0)

    async def get_summary_field(self, customer_name, first_day, last_day=None):
        if last_day is None:
            last_day = self._last_day_of_month(first_day)
        summary = await self.get_month_summary(customer_name, first_day, last_day)
        mon_name = first_day.strftime('%b')
        if summary == 0:
            avg = 0
        else:
            avg = summary / int(last_day.day)
        return mon_name, summary, avg


    async def get_report_data(self, customer_name, q_date):
        customer_data = await self.get_current_date_data(customer_name, q_date)
        report_data = {
            'customer_name': customer_data['customer_name'],
            'date': customer_data['date'],
        }
        for field, preparator in self.prepare_data.items():
            report_data[field] = await self.prepare_data.get(field)(self, customer_data)

        report_data['monthly_data'] = []
        q_date_obj = datetime.datetime.strptime(q_date, '%Y-%m-%d')

        current_month_fd = q_date_obj.replace(day=1)
        previous_month_fd = (current_month_fd.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        previous2_month_fd = (previous_month_fd.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        previous3_month_fd = (previous2_month_fd.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)

        prev_months = [previous_month_fd, previous2_month_fd, previous3_month_fd]
        prev_months.reverse()
        for m in prev_months:
            month_data = await self.get_summary_field(
                customer_data['customer_name'],
                m,
                )
            report_data['monthly_data'].append(month_data)

        current_month_sum = await self.get_summary_field(customer_data['customer_name'],
            current_month_fd, q_date_obj)
        report_data['monthly_data'].append(current_month_sum)
        return report_data

    async def prepare_daily_traffic(self, customer_data):
        date_list = [
            customer_data['date'] - datetime.timedelta(days=i) for i in range(23)
        ]
        date_list.reverse()
        daily_traffic_for_23_days = []
        for q_date in date_list:
            next_date = q_date + datetime.timedelta(days=1)

            filt = {
                'customer_name': customer_data['customer_name'],
                'date': {
                    '$gte': q_date,
                    '$lt': next_date
                }
            }
            projection = {'daily_traffic': True, 'date': True, '_id': False}
            daily_traffic = await self.report_collection.find_one(filt, projection)
            daily_traffic_for_23_days.append(daily_traffic)
        return {
            'x': [
                item.get('date').strftime('%d-%b') for item in daily_traffic_for_23_days if item
            ],
            'y': [item.get('daily_traffic') for item in daily_traffic_for_23_days if item],
        }

    async def prepare_daily_traffic_by_hour(self, customer_data):
        t_fmt = '%H:%M'
        prepare_time = lambda x: x.strftime(t_fmt)
        return {
            'x': [
                prepare_time(item.get('time'))
                for item in customer_data['daily_traffic_by_hour']
            ],
            'y': [
                item.get('bb_gbps_total')
                for item in customer_data['daily_traffic_by_hour']
            ],
        }

    async def prepare_traffic_dist(self, customer_data):
        return {
            'x': [i.get('pop') for i in customer_data['traffic_dist']],
            'y': [i.get('bb_b_total') for i in customer_data['traffic_dist']],
        }

    async def prepare_monthly_data(self, data):
        return None

    prepare_data = {
        'daily_traffic': prepare_daily_traffic,
        'daily_traffic_by_hour': prepare_daily_traffic_by_hour,
        'traffic_dist': prepare_traffic_dist,
    }
