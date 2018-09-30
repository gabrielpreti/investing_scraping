import investing_scrapping
import urllib3
from lxml import html
import logging
import time
from pymongo import MongoClient
import getopt
import sys

MONGO_HOST = None
if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["mongohost="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('--mongohost'):
            MONGO_HOST = arg
else:
    MONGO_HOST = 'localhost'



mongo_client = MongoClient(MONGO_HOST, 27017)
mongo_database = mongo_client.stoch_data_database
investing_data_collection = mongo_database.investing_collection
http_connection_pool = urllib3.PoolManager()
LOG = logging.getLogger(investing_scrapping.LOGGER_NAME)

req = http_connection_pool.request(method='GET', url='https://br.investing.com/equities/StocksFilter', headers={'User-Agent': investing_scrapping.USER_AGENT})
html_tree = html.fromstring(req.data.decode('utf-8'))

stock_links_list = html_tree.xpath("//table[@id='cross_rate_markets_stocks_1']/tbody/tr/td[2]/a")
for stock_link in stock_links_list:
    stock = stock_link.get('href').split('/')[-1]
    LOG.info("Processing stock %s", stock)
    data = investing_scrapping.get_stock_info_dict(http_connection_pool, stock)
    print(data)
    investing_data_collection.insert_one(data)
    time.sleep(30)