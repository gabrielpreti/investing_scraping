import investing_scrapping
import urllib3
from lxml import html
import logging
import time
from pymongo import MongoClient
import getopt
import sys
import datetime

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



# import json
# MONGO_HOST = '54.159.207.238'
# mongo_client = MongoClient(MONGO_HOST, 27017)
# mongo_database = mongo_client.stoch_data_database
# investing_data_collection = mongo_database.investing_collection
# cursor = investing_data_collection.find()
# size = investing_data_collection.count_documents({})
# # docs = list(cursor)
# data_file_name = 'investing_data_collection-%s.json' % datetime.datetime.now().strftime('%Y-%m-%d')
# with open(data_file_name, "w") as file:
#     file.write('[')
#     for i, document in enumerate(cursor, 1):
#         if '_id' in list(document.keys()):
#             del document['_id']
#         file.write(json.dumps(document, default=str))
#         file.write("\n")
#         if i != size:
#             file.write(',')
#     file.write(']')
#
# docs = None
# with open(data_file_name, "r") as file:
#     docs = json.load(file)
# len(docs)
#
# i = 1
# while i<200:
#     doc = docs[-1*i]
#     if 'General-Information' in doc.keys() and 'code' in doc['General-Information'].keys() and  doc['General-Information']['code'] == 'RAIL3':
#         print(doc)
#         break
#     i = i+1
