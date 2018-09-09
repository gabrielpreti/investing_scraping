import investing_scrapping
import urllib3
from lxml import html
import logging
import time

LOG = logging.getLogger(investing_scrapping.LOGGER_NAME)
http_connection_pool = urllib3.PoolManager()

req = http_connection_pool.request(method='GET', url='https://br.investing.com/equities/StocksFilter', headers={'User-Agent': investing_scrapping.USER_AGENT})
html_tree = html.fromstring(req.data.decode('utf-8'))

stock_links_list = html_tree.xpath("//table[@id='cross_rate_markets_stocks_1']/tbody/tr/td[2]/a")
for stock_link in stock_links_list:
    stock = stock_link.get('href').split('/')[-1]
    LOG.info("Processing stock %s", stock)
    print(investing_scrapping.get_stock_info_json(http_connection_pool, stock))
    time.sleep(5)