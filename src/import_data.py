#!/usr/bin/env python3
import asyncio
import datetime
import logging
from itertools import zip_longest  # for Python 3.x

import sqlalchemy
from pytz import timezone

fmt_mysql_date = lambda d: d.date().strftime('%Y-%m-%d %H:%M:%S')


class DataImporter:
    tz = timezone('MST')

    def __init__(self, engine, issue_engine, mongo_client, logger=None):
        self.get_from_mysql = {
            'daily_traffic': self.get_daily_traffic,
            'daily_traffic_by_hour': self.get_daily_traffic_by_hour,
            'traffic_dist': self.get_traffic_dist,
            # 'monthly_data': self.get_monthly_data,
            # 'issues': self.get_issues,
        }
        self.engine = engine
        self.issue_engine = issue_engine
        self.mongo_client = mongo_client
        self.mongo_db = self.mongo_client['customer_report']
        self.report_collection = self.mongo_db['customer_data']
        self.logger = logging.getLogger('DataImporter') if logger is None else logger

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get_data(self, q_date):
        self.logger.info(f'Start fetching data for {q_date}')
        dt, dth, td = await asyncio.gather(
            *[self.query_db(field=f, q_date=q_date) for f in self.get_from_mysql.keys()])
        self.logger.debug(f'Processing data for {q_date}')
        customers = []
        customer_names = [i.customer_name for i in dt]
        for customer_name in customer_names:
            customer = {'customer_name': customer_name, 'date': q_date}

            try:
                customer['daily_traffic'] = next(
                    i for i in dt if i.customer_name == customer_name).bb_b_total
            except StopIteration:
                self.logger.exception(
                    f'No daily traffic found for {customer_name} {q_date}')
                raise

            try:
                customer['daily_traffic_by_hour'] = [{
                    'time': datetime.datetime.fromtimestamp(i.time, tz=self.tz),
                    'bb_gbps_total': i.bb_gbps_total
                } for i in dth if i.customer_name == customer_name]
            except Exception:
                self.logger.exception('Exception occured while processing daily traffic '
                                      f'by hour for {customer_name} {q_date}')
                raise

            try:
                customer['traffic_dist'] = [{
                    'pop': i.pop,
                    'bb_b_total': i.bb_b_total
                } for i in td if i.customer_name == customer_name]
            except Exception:
                self.logger.exception(
                    'Exception occured while processing traffic distribution'
                    f'by hour for {customer_name} {q_date}')
                raise

            customers.append(customer)

        for customer in customers:
            self.logger.debug(
                f'Updating data for {customer["customer_name"]} {q_date} in mongo.')
            next_date = q_date + datetime.timedelta(days=1)
            filt = {
                'customer_name': customer['customer_name'],
                'date': {
                    '$gte': q_date,
                    '$lt': next_date
                }
            }
            try:
                await self.report_collection.update_one(filt, {'$setOnInsert': customer},
                                                        upsert=True)
            except Exception:
                self.logger.exception('Exception occured while updating data in mongo '
                                      f'for {customer_name} {q_date}')
                raise
        self.logger.info(f'Finished fetching data for {q_date}')
        return

    async def make_text_query(self, query_str):
        async with self.engine.acquire() as conn:
            query = await conn.execute(sqlalchemy.text(query_str))
            return await query.fetchall()

    async def get_daily_traffic_by_hour(self, q_date):
        current_date = fmt_mysql_date(q_date)
        next_date = fmt_mysql_date(q_date + datetime.timedelta(days=1))
        q_str = ('SELECT customer_name, time, bb_gbps_total '
                 'FROM smc_billing_data.5min_customer_peak_day '
                 f'WHERE created_date>="{current_date}" AND created_date<"{next_date}" '
                 f' ORDER BY time;')
        try:
            result = await self.make_text_query(q_str)
        except Exception:
            self.logger.exception(
                'Exception occured while fetching daily traffic by hour '
                f'for {q_date}')
            raise
        return result

    async def get_traffic_dist(self, q_date):
        current_date = fmt_mysql_date(q_date)
        next_date = fmt_mysql_date(q_date + datetime.timedelta(days=1))
        q_str = ('SELECT customer_name, pop, SUM(bb_b_total) as bb_b_total'
                 ' FROM billing_data_join_day '
                 f'WHERE created_date>="{current_date}" AND created_date<"{next_date}" '
                 ' GROUP BY created_date, pop, customer_name ORDER BY bb_b_total ASC;')
        try:
            result = await self.make_text_query(q_str)
        except Exception:
            self.logger.exception('Exception occured while fetching traffic distribution '
                                  f'for {q_date}')
            raise
        return result

    async def get_daily_traffic(self, q_date):
        # ago_23 = fmt_mysql_date(q_date - datetime.timedelta(days=23))
        current_date = fmt_mysql_date(q_date)
        next_date = fmt_mysql_date(q_date + datetime.timedelta(days=1))
        q_str = (
            'SELECT bb_b_total, customer_name '
            'FROM smc_billing_data.view_created_date_customer '
            #  f'WHERE created_date>"{ago_23}" '
            f'WHERE created_date>="{current_date}" AND created_date<"{next_date}" '
            'ORDER BY created_date;')
        try:
            result = await self.make_text_query(q_str)
        except Exception:
            self.logger.exception('Exception occured while fetching daily traffic '
                                  f'for {q_date}')
            raise
        return result

    # async def get_monthly_data(self, q_date):
    #     ago_125 = fmt_mysql_date(q_date - datetime.timedelta(days=125))
    #     q_str = ('SELECT created_date, customer_name, SUM(bb_b_total) as bb_b_total '
    #              'FROM smc_billing_data.view_created_date_customer '
    #              f'WHERE created_date<"{ago_125}" '
    #              'GROUP BY MONTH(created_date) '
    #              'ORDER BY created_date;')
    #     return await self.make_text_query(q_str)

    async def query_db(self, q_date, field):
        data = await self.get_from_mysql.get(field)(q_date)
        return data


if __name__ == '__main__':
    import argparse
    import configparser
    import logging.handlers
    import sys

    from aiomysql.sa import create_engine
    import motor.motor_asyncio
    import pymysql.err

    sys.path.insert(0, '..')

    parser = argparse.ArgumentParser()
    parser.add_argument('days', type=int, default=2)
    parser.add_argument('--logfile', default='import_data.log')
    parser.add_argument('--chunk_size', type=int, default=15)
    args = parser.parse_args()

    file_handler = logging.handlers.TimedRotatingFileHandler(args.logfile, when='D')
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M', handlers=(console_handler, file_handler))
    logger = logging.getLogger('DataImporter')

    config = configparser.ConfigParser()
    config.read('config.ini')

    def make_slices(n, iterable, fill=None):
        return zip_longest(*[iter(iterable)] * n, fillvalue=fill)

    async def main():
        mysql_config = config['mysql']
        logger.debug('Creating MySQL connections.')
        try:
            engine = await create_engine(
                user=mysql_config['user'],
                db=mysql_config['db'],
                host=mysql_config['host'],
                port=int(mysql_config['port']),
                password=mysql_config['password'],
                minsize=10,
                maxsize=20,
            )
            issue_engine = await create_engine(
                user=mysql_config['user'],
                db=mysql_config['db'],
                host=mysql_config['host'],
                port=int(mysql_config['port']),
                password=mysql_config['password'],
                minsize=10,
                maxsize=20,
            )
        except pymysql.err.OperationalError:
            logger.exception('Exception occured while creating connection to MySQL')
            raise

        mongo_config = config['mongo']
        logger.debug('Creating MongoDB connections.')
        try:
            mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_config['address'])
        except Exception:
            logger.exception('Exception occured while creating connection to MongoDB')
            raise

        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        date_list = [yesterday - datetime.timedelta(days=i) for i in range(args.days)]
        for date_range in make_slices(args.chunk_size, date_list):
            async with DataImporter(engine, issue_engine, mongo_client,
                                    logger) as importer:
                await asyncio.gather(*[
                    importer.get_data(q_date)
                    for q_date in date_range
                    if q_date is not None
                ])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
