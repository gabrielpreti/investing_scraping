import urllib3
import re
from lxml import html
import json
import unicodedata
import sys
import logging

LOGGER_NAME = 'investing_scrapping'
BASE_URL = "https://br.investing.com/equities"
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'

LOG_LEVEL = logging.INFO
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LOG_LEVEL)
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(LOG_LEVEL)
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)


#######################################################################################################################
#######################################################################################################################
def normalize_and_encode(str):
    return unicodedata.normalize('NFKD', str).encode('ascii','ignore')

def generate_html_tree(connectionpool, url, httpmethod='GET', headers={'User-Agent': USER_AGENT}, fields=None):
    LOG = logging.getLogger(LOGGER_NAME)
    req = connectionpool.request(method=httpmethod, url=url, headers=headers, fields=fields)
    LOG.debug("HTTP code %s for url %s", req.status, url)
    return html.fromstring(normalize_and_encode(req.data.decode('utf-8')))


####Geral/Informação
def parse_stock_general_information(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    general_information_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s" % (BASE_URL, stock))
    data = html_tree.xpath('//div[@class="instrumentHead"]/h1[@itemprop="name"]')[0].text_content()
    stockcode = re.search("\((.*)\)", data).group(1)
    general_information_data['code'] = stockcode
    LOG.debug("%s=%s" % ("code", stockcode))

    data = html_tree.xpath(
        '//div[@class="clear overviewDataTable overviewDataTableWithTooltip"]//div[@class="inlineblock"] | //div[@class="first inlineblock"]')
    for div in data:
        general_information_data[div.getchildren()[0].text_content().strip()] = div.getchildren()[1].text_content().strip()

    return general_information_data


####Geral/Perfil
def parse_stock_general_information(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    general_profile_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s-company-profile" % (BASE_URL, stock))
    data = html_tree.xpath('//div[@class="companyProfileHeader"]/div')
    for div in data:
        prop = div.text
        value = div.text_content().replace(prop, '')
        general_profile_data[prop] = value
        LOG.debug("%s=%s" % (prop, value))

    return general_profile_data


####Finanças/Finanças
def parse_stock_finance_finance(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_finance_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s-financial-summary" % (BASE_URL, stock))
    summaries = html_tree.xpath('//div[@id="rsdiv"]/div[@class="companySummaryIncomeStatement"]')
    for summary in summaries:
        title = summary.xpath('h3/a')[0].text_content().strip()
        title = " ".join(title.split()[1:])
        finance_finance_data[title] = {}
        LOG.debug(title)

        data = summary.xpath('div[@class="info float_lang_base_2"]/div[@class="infoLine"]')
        for div in data:
            spans = div.getchildren()
            item, value, complement = (spans[0].text_content().strip(), spans[2].text_content().strip(), spans[1].text_content().strip())
            LOG.debug("\t%s=%s\t%s" % (item, value, complement))
            finance_finance_data[title][item] = (value, complement)

        data = summary.xpath('table[@class="genTbl openTbl companyFinancialSummaryTbl"]/thead//th')
        encerramentos_exercicios = [d.text_content().strip() for d in data[1:]]
        data = summary.xpath('table[@class="genTbl openTbl companyFinancialSummaryTbl"]/tbody/tr')
        for tr in data:
            trchildrens = tr.getchildren()
            item = trchildrens[0].text_content().strip()
            finance_finance_data[title][item] = {}
            LOG.debug('\t' + item)
            for e, v in zip(encerramentos_exercicios, tr.getchildren()[1:]):
                finance_finance_data[title][item][e] = v.text_content().strip()
                LOG.debug("\t\t%s=%s" % (e, v.text_content().strip()))
    return finance_finance_data


####Finanças/Demonstrações
def finance_demonstrations(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_demonstrations_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-income-statement' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content().strip()
        finance_demonstrations_data[item_name] = {}
        LOG.debug(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            finance_demonstrations_data[item_name][e] = v.text_content().strip()
            LOG.debug("\tExercicio=%s:\t%s" % (e, v.text_content().strip()))
    return finance_demonstrations_data


####Finanças/Balanço Patrimonial
def finance_balances(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_balances_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-balance-sheet' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content().strip()
        finance_balances_data[item_name] = {}
        LOG.debug(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            finance_balances_data[item_name][e] = v.text_content().strip()
            LOG.debug("\tExercicio=%s:\t%s" % (e, v.text_content().strip()))
    return finance_balances_data


####Finanças/Fluxo de Caixa
def finance_cash_flow(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_cashflow_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-cash-flow' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content().strip()
        finance_cashflow_data[item_name] = {}
        LOG.debug(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            finance_cashflow_data[item_name][e] = v.text_content().strip()
            LOG.debug("\tExercicio=%s:\t%s" % (e, v.text_content().strip()))
    return finance_cashflow_data


####Finanças/Indicadores
def finance_indicators(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_indicators_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-ratios' % (BASE_URL, stock))
    escopo_indicadores = [x.text_content().strip() for x in html_tree.xpath('//table[@id="rrTable"]/thead/tr/th')[1:]]
    indicadores = html_tree.xpath('//table[@id="rrTable"]/tbody/tr[@id="childTr"]/td/div/table/tbody/tr/td/span/../..')
    for indicador in indicadores:
        indicator_name = indicador.getchildren()[0].text_content().strip()
        finance_indicators_data[indicator_name] = {}
        LOG.debug(indicator_name)
        for e, i in zip(escopo_indicadores, indicador.getchildren()[1:]):
            finance_indicators_data[indicator_name][e] = i.text_content().strip()
            LOG.debug("\t%s=%s" % (e, i.text_content().strip()))
    return finance_indicators_data


####Finanças/Lucros
def finance_profits(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_profits_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-earnings' % (BASE_URL, stock))
    columns = [col.text_content().replace("/", "").strip() for col in
               html_tree.xpath('//table[@class="genTbl openTbl ecoCalTbl earnings earningsPageTbl"]/thead/tr/th[text()]')]
    earningshistory = html_tree.xpath('//tr[@name="instrumentEarningsHistory"]')
    for history in earningshistory:
        exercise_date = history.getchildren()[1].text_content().strip()
        finance_profits_data[exercise_date] = {}
        LOG.debug("Exercício=" + exercise_date)
        for c, h in zip(columns, history.getchildren()):
            value = h.text_content().replace("/", "").strip() if h.text_content().startswith("/") else h.text_content().strip()
            finance_profits_data[exercise_date][c] = value
            LOG.debug("\t%s=%s" % (c, value))
    return finance_profits_data

####Técnica/Análise Técnica
def technical_technical_analysis(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    technical_analysis_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-technical' % (BASE_URL, stock))
    periods = [(p.text_content(), p.get('pairid'), p.get('data-period')) for p in
               html_tree.xpath('//div[@id="technicalstudiesSubTabs"]/ul/li')]
    for period in periods:
        period_name = period[0]
        technical_analysis_data[period_name] = {}
        LOG.debug(period_name)
        html_tree = generate_html_tree(connectionpool=http_connection_pool, httpmethod='POST',
                                       url='https://br.investing.com/instruments/Service/GetTechincalData',
                                       headers={'User-Agent': USER_AGENT, 'X-Requested-With': 'XMLHttpRequest'},
                                       fields={'pairID': period[1], 'period': period[2]})

        tech_summary_div = html_tree.xpath('//div[@id="techStudiesInnerWrap"]')[0]

        summary = tech_summary_div.xpath('//div[@class="summary"]/span[1]')[0].text_content()
        technical_analysis_data[period_name]['Resumo']={}
        technical_analysis_data[period_name]['Resumo']['Resumo']=summary
        LOG.debug('\tResumo=%s' % (summary))

        for summary_table_line in tech_summary_div.xpath('div[@class="summaryTableLine"]'):
            name, value = (summary_table_line[0].text_content().replace(':', ''), summary_table_line[1].text_content())
            technical_analysis_data[period_name]['Resumo'][name]={}

            technical_analysis_data[period_name]['Resumo'][name]['Resumo']=value
            LOG.debug("\t\t%s=%s" % (name, value))

            moving_avg_summ = summary_table_line[2].getchildren()
            x, y = (moving_avg_summ[0].text_content(), moving_avg_summ[1].text_content().replace('(', '').replace(')', ''))
            technical_analysis_data[period_name]['Resumo'][name][x]=y
            LOG.debug("\t\t\t%s=%s" % (x, y))

            tech_indicators_sum = summary_table_line[3].getchildren()
            x, y = (tech_indicators_sum[0].text_content(), tech_indicators_sum[1].text_content().replace('(', '').replace(')', ''))
            technical_analysis_data[period_name]['Resumo'][name][x] = y
            LOG.debug("\t\t\t%s=%s" % (x, y))

        technical_analysis_data[period_name]['Pontos de Pivot'] = {}
        LOG.debug("\tPontos de Pivot")
        pivot_points_table = html_tree.xpath('//table[@id="curr_table"]')[0]
        headers = [x.text_content().strip() for x in pivot_points_table.xpath('thead/tr/th')[1:]]
        pivot_indicators = pivot_points_table.xpath('tbody/tr')
        for indicator in pivot_indicators:
            indicator_name = indicator.getchildren()[0].text_content().strip()
            technical_analysis_data[period_name]['Pontos de Pivot'][indicator_name]={}
            LOG.debug("\t\t%s" % (indicator_name))
            for h, i in zip(headers, indicator.getchildren()[1:]):
                technical_analysis_data[period_name]['Pontos de Pivot'][indicator_name][h]=i.text_content().strip()
                LOG.debug("\t\t\t%s=%s" % (h, i.text_content()))

        technical_analysis_data[period_name]['Indicadores Técnicos']={}
        LOG.debug("\tIndicadores Técnicos")
        tech_indicators_table = html_tree.xpath('//table[@id="curr_table"]')[1]
        headers = [x.text_content().strip() for x in tech_indicators_table.xpath('thead/tr/th')[1:]]
        tech_indicators = tech_indicators_table.xpath('tbody/tr')
        for indicator in tech_indicators[:-1]:
            indicator_name = indicator.getchildren()[0].text_content()
            technical_analysis_data[period_name]['Indicadores Técnicos'][indicator_name]={}
            LOG.debug("\t\t%s" % (indicator_name))
            for h, i in zip(headers, indicator.getchildren()[1:]):
                technical_analysis_data[period_name]['Indicadores Técnicos'][indicator_name][h]=i.text_content().strip()
                LOG.debug("\t\t\t%s=%s" % (h, i.text_content().strip()))
        technical_analysis_data[period_name]['Indicadores Técnicos']['Total'] = {}
        LOG.debug("\t\tTotal")
        for p in tech_indicators_table.xpath('tbody/tr[last()]/td/p')[:-1]:
            p_children = p.getchildren()
            x, y = p_children[0].text_content().strip().replace(':', ''), p_children[1].text_content().strip()
            technical_analysis_data[period_name]['Indicadores Técnicos']['Total'][x]=y
            LOG.debug("\t\t\t%s=%s" % (x, y))
        x = tech_indicators_table.xpath('tbody/tr[last()]/td/p[last()]/span')[0].text_content().strip()
        technical_analysis_data[period_name]['Indicadores Técnicos']['Total']['Resumo']=x
        LOG.debug("\t\t\tResumo=%s" % (x))

        technical_analysis_data[period_name]['Médias Móveis'] = {}
        LOG.debug("\tMédias Móveis")
        moving_avg_table = html_tree.xpath('//table[@id="curr_table"]')[2]
        headers = [x.text_content().strip() for x in moving_avg_table.xpath('thead/tr/th')[1:]]
        moving_avgs = moving_avg_table.xpath('tbody/tr')
        for mavg in moving_avgs[:-1]:
            mavgname = mavg.getchildren()[0].text_content().strip()
            technical_analysis_data[period_name]['Médias Móveis'][mavgname]={}
            LOG.debug("\t\t%s" % (mavgname))
            for h, v in zip(headers, mavg.getchildren()[1:]):
                technical_analysis_data[period_name]['Médias Móveis'][mavgname][h]={}
                LOG.debug("\t\t\t%s" % (h))

                value = v.xpath('span/..')[0].text.strip()
                technical_analysis_data[period_name]['Médias Móveis'][mavgname][h]['Valor']=value
                LOG.debug("\t\t\t\tValor=%s" % (value))

                action = v.xpath('span')[0].text.strip()
                technical_analysis_data[period_name]['Médias Móveis'][mavgname][h][
                    'Ação'] = action
                LOG.debug("\t\t\t\tAção=%s" % (action))
        technical_analysis_data[period_name]['Médias Móveis']['Total']={}
        LOG.debug("\t\tTotal")
        for p in moving_avg_table.xpath('tbody/tr[last()]/td/p')[:-1]:
            p_children = p.getchildren()
            x, y = (p_children[0].text_content().strip().replace(':', ''), p_children[1].text_content().strip())
            technical_analysis_data[period_name]['Médias Móveis']['Total'][x]=y
            LOG.debug("\t\t\t%s=%s" % (x, y))
        y = tech_indicators_table.xpath('tbody/tr[last()]/td/p[last()]/span')[0].text_content().strip()
        technical_analysis_data[period_name]['Médias Móveis']['Total']['Resumo']=y
        LOG.debug("\t\t\tResumo=%s" % (y))

    return technical_analysis_data

####Técnica/Padrão de Candlestick
def technical_candlestick_pattern(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    tecnical_candlestick_pattern_data = {'Candlestick Patterns': {}}
    candlestick_map = tecnical_candlestick_pattern_data['Candlestick Patterns']
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-candlestick' % (BASE_URL, stock))
    candlestick_patterns_table = html_tree.xpath('//table[@class="genTbl closedTbl ecoCalTbl patternTable js-csp-table"]')[
        0]
    headers = [x.text_content().strip() for x in candlestick_patterns_table.xpath('thead/tr/th')]
    patterns = candlestick_patterns_table.xpath('tbody/tr[@id]')
    for p in patterns:
        values = p.getchildren()
        name = values[1].text_content()
        candlestick_map[name] = {}
        current_map = candlestick_map[name]
        LOG.debug(name)

        x, y = headers[0], values[0].get('title')
        current_map[x] = y
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[1], values[2].text_content()
        current_map[x] = y
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[2], values[3].get('title')
        current_map[x] = y
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[3], values[4].text_content()
        current_map[x] = y
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[4], values[5].text_content() if len(values) == 6 else ""
        current_map[x] = y
        LOG.debug("\t%s=%s" % (x, y))
    return tecnical_candlestick_pattern_data

####Técnica/Estimativas Consensuais
def consensual_estimates(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    consensual_estimates_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-consensus-estimates' % (BASE_URL, stock))
    chart_div = html_tree.xpath("//div[@class='graphChart']")[0]
    name = chart_div.xpath("p[@class='chartSmalltitle']")[0].text_content().strip()
    consensual_estimates_data[name]={}
    LOG.debug(name)
    labels = chart_div.xpath("div[@class='yLabels']/p[@class='yLabel']")
    for l in labels:
        texts = l.text_content().split('|')
        consensual_estimates_data[name][texts[0].strip()] = texts[1].strip()
        LOG.debug("\t%s=%s" % (texts[0].strip(), texts[1].strip()))
    return consensual_estimates_data
##########################################################################################################################
def __get_info(name, fun, *args):
    LOG = logging.getLogger(LOGGER_NAME)
    try:
        return (name, fun(*args))
    except:
        LOG.exception("Error getting %s", name)
        return (name, {})

def get_stock_info_json(connectionpool, stock):
    stock_info = {}

    infos = {'General-Information': parse_stock_general_information,
             'Finance-Finance': parse_stock_finance_finance,
             'Finance-Demonstrations': finance_demonstrations,
             'Finance-Balances': finance_balances,
             'Finance-CashFlow': finance_cash_flow,
             'Finance-Indicators': finance_indicators,
             'Finance-Profits': finance_profits,
             'Technical-TechnicalAnalysis': technical_technical_analysis,
             'Technical-CandlestickPattern': technical_candlestick_pattern,
             'Technical-ConsensualEstimates': consensual_estimates}
    for k in infos.keys():
        info = __get_info(k, infos[k], connectionpool, stock)
        stock_info[info[0]] = info[1]
    return json.dumps(stock_info)


LOG = logging.getLogger(LOGGER_NAME)
http_connection_pool = urllib3.PoolManager()

req = http_connection_pool.request(method='GET', url='https://br.investing.com/equities/StocksFilter', headers={'User-Agent': USER_AGENT})
html_tree = html.fromstring(req.data.decode('utf-8'))

stock_links_list = html_tree.xpath("//table[@id='cross_rate_markets_stocks_1']/tbody/tr/td[2]/a")
for stock_link in stock_links_list:
    stock = stock_link.get('href').split('/')[-1]
    LOG.info("Processing stock %s", stock)
    print(get_stock_info_json(http_connection_pool, stock))

