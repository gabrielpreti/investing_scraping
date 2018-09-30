import re
from lxml import html
import json
import unicodedata
import time
import sys
import logging
import logging.config
import datetime

BASE_URL = "https://br.investing.com/equities"
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'

#################Logging configuration
LOGGER_NAME = 'investing_scrapping'
logging.config.fileConfig('logging.ini')


#######################################################################################################################
#######################################################################################################################
def set_dict_key_value(d, key, value):
    key = key.replace('.', '').strip()
    value = value.strip() if isinstance(value, basestring) else value
    d[key] = value

    return value

def normalize_and_encode(str):
    return unicodedata.normalize('NFKD', str).encode('ascii','ignore')

def generate_html_tree(connectionpool, url, httpmethod='GET', headers={'User-Agent': USER_AGENT}, fields=None):
    LOG = logging.getLogger(LOGGER_NAME)
    req = connectionpool.request(method=httpmethod, url=url, headers=headers, fields=fields)

    if req.status != 200:
        LOG.error("HTTP code %s for url %s", req.status, url)
    else:
        LOG.debug("HTTP code %s for url %s", req.status, url)

    return html.fromstring(normalize_and_encode(req.data.decode('utf-8')))


####Geral/Informacao
def parse_stock_general_information(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    general_information_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s" % (BASE_URL, stock))
    data = html_tree.xpath('//div[@class="instrumentHead"]/h1[@itemprop="name"]')[0].text_content()
    stockcode = re.search("\((.*)\)", data).group(1)
    set_dict_key_value(general_information_data, 'code', stockcode)
    LOG.debug("%s=%s" % ("code", stockcode))

    data = html_tree.xpath(
        '//div[@class="clear overviewDataTable overviewDataTableWithTooltip"]//div[@class="inlineblock"] | //div[@class="first inlineblock"]')
    for div in data:
        set_dict_key_value(general_information_data, div.getchildren()[0].text_content(), div.getchildren()[1].text_content())

    return general_information_data


####Geral/Perfil
def parse_stock_general_profile(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    general_profile_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s-company-profile" % (BASE_URL, stock))
    data = html_tree.xpath('//div[@class="companyProfileHeader"]/div')
    for div in data:
        prop = div.text
        value = div.text_content().replace(prop, '')
        set_dict_key_value(general_profile_data, prop, value)
        LOG.debug("%s=%s" % (prop, value))

    return general_profile_data


####Financas/Financas
def parse_stock_finance_finance(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_finance_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s-financial-summary" % (BASE_URL, stock))
    summaries = html_tree.xpath('//div[@id="rsdiv"]/div[@class="companySummaryIncomeStatement"]')
    for summary in summaries:
        title = summary.xpath('h3/a')[0].text_content()
        title_dict = set_dict_key_value(finance_finance_data, title, {})
        LOG.debug(title)

        data = summary.xpath('div[@class="info float_lang_base_2"]/div[@class="infoLine"]')
        for div in data:
            spans = div.getchildren()
            item, value, complement = (spans[0].text_content(), spans[2].text_content().strip(), spans[1].text_content().strip())
            LOG.debug("\t%s=%s\t%s" % (item, value, complement))
            set_dict_key_value(title_dict, item, (value, complement))

        data = summary.xpath('table[@class="genTbl openTbl companyFinancialSummaryTbl"]/thead//th')
        encerramentos_exercicios = [d.text_content().strip() for d in data[1:]]
        data = summary.xpath('table[@class="genTbl openTbl companyFinancialSummaryTbl"]/tbody/tr')
        for tr in data:
            trchildrens = tr.getchildren()
            item = trchildrens[0].text_content()
            item_dict = set_dict_key_value(title_dict, item, {})
            LOG.debug('\t' + item)
            for e, v in zip(encerramentos_exercicios, tr.getchildren()[1:]):
                set_dict_key_value(item_dict, e, v.text_content())
                LOG.debug("\t\t%s=%s" % (e, v.text_content().strip()))
    return finance_finance_data


####Financas/Demonstracoes
def finance_demonstrations(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_demonstrations_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-income-statement' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content()
        itemname_dict = set_dict_key_value(finance_demonstrations_data, item_name, {})
        LOG.debug(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            set_dict_key_value(itemname_dict, e, v.text_content())
            LOG.debug("\tExercicio=%s:\t%s" % (e, v.text_content()))
    return finance_demonstrations_data


####Financas/Balanco Patrimonial
def finance_balances(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_balances_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-balance-sheet' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content()
        itemname_dict = set_dict_key_value(finance_balances_data, item_name, {})
        LOG.debug(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            set_dict_key_value(itemname_dict, e, v.text_content())
            LOG.debug("\tExercicio=%s:\t%s" % (e, v.text_content()))
    return finance_balances_data


####Financas/Fluxo de Caixa
def finance_cash_flow(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_cashflow_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-cash-flow' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content()
        itemname_dict = set_dict_key_value(finance_cashflow_data, item_name, {})
        LOG.debug(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            set_dict_key_value(itemname_dict, e, v.text_content())
            LOG.debug("\tExercicio=%s:\t%s" % (e, v.text_content()))
    return finance_cashflow_data


####Financas/Indicadores
def finance_indicators(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_indicators_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-ratios' % (BASE_URL, stock))
    escopo_indicadores = [x.text_content().strip() for x in html_tree.xpath('//table[@id="rrTable"]/thead/tr/th')[1:]]
    indicadores = html_tree.xpath('//table[@id="rrTable"]/tbody/tr[@id="childTr"]/td/div/table/tbody/tr/td/span/../..')
    for indicador in indicadores:
        indicator_name = indicador.getchildren()[0].text_content()
        indicatorname_dict = set_dict_key_value(finance_indicators_data, indicator_name, {})
        LOG.debug(indicator_name)
        for e, i in zip(escopo_indicadores, indicador.getchildren()[1:]):
            set_dict_key_value(indicatorname_dict, e, i.text_content())
            LOG.debug("\t%s=%s" % (e, i.text_content()))
    return finance_indicators_data


####Financas/Lucros
def finance_profits(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    finance_profits_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-earnings' % (BASE_URL, stock))
    columns = [col.text_content().replace("/", "").strip() for col in
               html_tree.xpath('//table[@class="genTbl openTbl ecoCalTbl earnings earningsPageTbl"]/thead/tr/th[text()]')]
    earningshistory = html_tree.xpath('//tr[@name="instrumentEarningsHistory"]')
    for history in earningshistory:
        exercise_date = history.getchildren()[1].text_content()
        exercisedate_dict = set_dict_key_value(finance_profits_data, exercise_date, {})
        LOG.debug("Exercicio=" + exercise_date)
        for c, h in zip(columns, history.getchildren()):
            value = h.text_content().replace("/", "").strip() if h.text_content().startswith("/") else h.text_content().strip()
            set_dict_key_value(exercisedate_dict, c, value)
            LOG.debug("\t%s=%s" % (c, value))
    return finance_profits_data

####Tecnica/Analise Tecnica
def technical_technical_analysis(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    technical_analysis_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-technical' % (BASE_URL, stock))
    periods = [(p.text_content(), p.get('pairid'), p.get('data-period')) for p in
               html_tree.xpath('//div[@id="technicalstudiesSubTabs"]/ul/li')]
    for period in periods:
        period_name = period[0]
        periodname_dict = set_dict_key_value(technical_analysis_data, period_name, {})
        LOG.debug(period_name)
        html_tree = generate_html_tree(connectionpool=connectionpool, httpmethod='POST',
                                       url='https://br.investing.com/instruments/Service/GetTechincalData',
                                       headers={'User-Agent': USER_AGENT, 'X-Requested-With': 'XMLHttpRequest'},
                                       fields={'pairID': period[1], 'period': period[2]})

        tech_summary_div = html_tree.xpath('//div[@id="techStudiesInnerWrap"]')[0]

        summary = tech_summary_div.xpath('//div[@class="summary"]/span[1]')[0].text_content()
        periodname_resumo_dict = set_dict_key_value(periodname_dict, 'Resumo', {})
        set_dict_key_value(periodname_resumo_dict, 'Resumo', summary)
        LOG.debug('\tResumo=%s' % (summary))

        for summary_table_line in tech_summary_div.xpath('div[@class="summaryTableLine"]'):
            name, value = (summary_table_line[0].text_content().replace(':', ''), summary_table_line[1].text_content())
            periodname_resumo_name_dict = set_dict_key_value(periodname_resumo_dict, name, {})

            set_dict_key_value(periodname_resumo_name_dict, 'Resumo', value)
            LOG.debug("\t\t%s=%s" % (name, value))

            moving_avg_summ = summary_table_line[2].getchildren()
            x, y = (moving_avg_summ[0].text_content(), moving_avg_summ[1].text_content().replace('(', '').replace(')', ''))
            set_dict_key_value(periodname_resumo_name_dict, x, y)
            LOG.debug("\t\t\t%s=%s" % (x, y))

            tech_indicators_sum = summary_table_line[3].getchildren()
            x, y = (tech_indicators_sum[0].text_content(), tech_indicators_sum[1].text_content().replace('(', '').replace(')', ''))
            set_dict_key_value(periodname_resumo_name_dict, x, y)
            LOG.debug("\t\t\t%s=%s" % (x, y))

        periodname_pontospivot_dict = set_dict_key_value(periodname_dict, 'Pontos de Pivot', {})
        LOG.debug("\tPontos de Pivot")
        pivot_points_table = html_tree.xpath('//table[@id="curr_table"]')[0]
        headers = [x.text_content().strip() for x in pivot_points_table.xpath('thead/tr/th')[1:]]
        pivot_indicators = pivot_points_table.xpath('tbody/tr')
        for indicator in pivot_indicators:
            indicator_name = indicator.getchildren()[0].text_content()
            periodname_pontospivot_indicatorname_dict = set_dict_key_value(periodname_pontospivot_dict, indicator_name, {})
            LOG.debug("\t\t%s" % (indicator_name))
            for h, i in zip(headers, indicator.getchildren()[1:]):
                set_dict_key_value(periodname_pontospivot_indicatorname_dict, h, i.text_content())
                LOG.debug("\t\t\t%s=%s" % (h, i.text_content()))

        periodname_indicadorestecnicos_dict = set_dict_key_value(periodname_dict, 'Indicadores Tecnicos', {})
        LOG.debug("\tIndicadores Tecnicos")
        tech_indicators_table = html_tree.xpath('//table[@id="curr_table"]')[1]
        headers = [x.text_content().strip() for x in tech_indicators_table.xpath('thead/tr/th')[1:]]
        tech_indicators = tech_indicators_table.xpath('tbody/tr')
        for indicator in tech_indicators[:-1]:
            indicator_name = indicator.getchildren()[0].text_content()
            periodname_indicadorestecnicos_indicatorname_dict = set_dict_key_value(periodname_indicadorestecnicos_dict, indicator_name, {})
            LOG.debug("\t\t%s" % (indicator_name))
            for h, i in zip(headers, indicator.getchildren()[1:]):
                set_dict_key_value(periodname_indicadorestecnicos_indicatorname_dict, h, i.text_content())
                LOG.debug("\t\t\t%s=%s" % (h, i.text_content().strip()))
        periodname_indicadorestecnicos_total_dict = set_dict_key_value(periodname_indicadorestecnicos_dict, 'Total', {})
        LOG.debug("\t\tTotal")
        for p in tech_indicators_table.xpath('tbody/tr[last()]/td/p')[:-1]:
            p_children = p.getchildren()
            x, y = p_children[0].text_content().strip().replace(':', ''), p_children[1].text_content()
            set_dict_key_value(periodname_indicadorestecnicos_total_dict, x, y)
            LOG.debug("\t\t\t%s=%s" % (x, y))
        x = tech_indicators_table.xpath('tbody/tr[last()]/td/p[last()]/span')[0].text_content()
        set_dict_key_value(periodname_indicadorestecnicos_total_dict, 'Resumo', x)
        LOG.debug("\t\t\tResumo=%s" % (x))

        periodname_mediasmoveis_dict = set_dict_key_value(periodname_dict, 'Medias Moveis', {})
        LOG.debug("\tMedias Moveis")
        moving_avg_table = html_tree.xpath('//table[@id="curr_table"]')[2]
        headers = [x.text_content().strip() for x in moving_avg_table.xpath('thead/tr/th')[1:]]
        moving_avgs = moving_avg_table.xpath('tbody/tr')
        for mavg in moving_avgs[:-1]:
            mavgname = mavg.getchildren()[0].text_content()
            periodname_mediasmoveis_mavgname_dict = set_dict_key_value(periodname_mediasmoveis_dict, mavgname, {})
            LOG.debug("\t\t%s" % (mavgname))
            for h, v in zip(headers, mavg.getchildren()[1:]):
                periodname_mediasmoveis_mavgname_h_dict = set_dict_key_value(periodname_mediasmoveis_mavgname_dict, h, {})
                LOG.debug("\t\t\t%s" % (h))

                value = v.xpath('span/..')[0].text
                set_dict_key_value(periodname_mediasmoveis_mavgname_h_dict, 'Valor', value)
                LOG.debug("\t\t\t\tValor=%s" % (value))

                action = v.xpath('span')[0].text.strip()
                set_dict_key_value(periodname_mediasmoveis_mavgname_h_dict, 'Acao',  action)
                LOG.debug("\t\t\t\tAcao=%s" % (action))
        periodname_mediasmoveis_total_dict = set_dict_key_value(periodname_mediasmoveis_dict, 'Total', {})
        LOG.debug("\t\tTotal")
        for p in moving_avg_table.xpath('tbody/tr[last()]/td/p')[:-1]:
            p_children = p.getchildren()
            x, y = (p_children[0].text_content().strip().replace(':', ''), p_children[1].text_content())
            set_dict_key_value(periodname_mediasmoveis_total_dict, x, y)
            LOG.debug("\t\t\t%s=%s" % (x, y))
        y = tech_indicators_table.xpath('tbody/tr[last()]/td/p[last()]/span')[0].text_content().strip()
        set_dict_key_value(periodname_mediasmoveis_total_dict, 'Resumo', y)
        LOG.debug("\t\t\tResumo=%s" % (y))

    return technical_analysis_data

####Tecnica/Padrao de Candlestick
def technical_candlestick_pattern(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    tecnical_candlestick_pattern_data = {}
    candlestickpatterns_dict = set_dict_key_value(tecnical_candlestick_pattern_data, 'Candlestick Patterns', {})
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-candlestick' % (BASE_URL, stock))
    candlestick_patterns_table = html_tree.xpath('//table[@class="genTbl closedTbl ecoCalTbl patternTable js-csp-table"]')[
        0]
    headers = [x.text_content().strip() for x in candlestick_patterns_table.xpath('thead/tr/th')]
    patterns = candlestick_patterns_table.xpath('tbody/tr[@id]')
    for p in patterns:
        values = p.getchildren()
        name = values[1].text_content()
        candlesticpatterns_name_dict = set_dict_key_value(candlestickpatterns_dict, name, {})
        LOG.debug(name)

        x, y = headers[0], values[0].get('title')
        set_dict_key_value(candlesticpatterns_name_dict, x, y)
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[1], values[2].text_content()
        set_dict_key_value(candlesticpatterns_name_dict, x, y)
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[2], values[3].get('title')
        set_dict_key_value(candlesticpatterns_name_dict, x, y)
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[3], values[4].text_content()
        set_dict_key_value(candlesticpatterns_name_dict, x, y)
        LOG.debug("\t%s=%s" % (x, y))

        x, y = headers[4], values[5].text_content() if len(values) == 6 else ""
        set_dict_key_value(candlesticpatterns_name_dict, x, y)
        LOG.debug("\t%s=%s" % (x, y))
    return tecnical_candlestick_pattern_data

####Tecnica/Estimativas Consensuais
def consensual_estimates(connectionpool, stock):
    LOG = logging.getLogger(LOGGER_NAME)
    consensual_estimates_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-consensus-estimates' % (BASE_URL, stock))
    chart_div = html_tree.xpath("//div[@class='graphChart']")[0]
    name = chart_div.xpath("p[@class='chartSmalltitle']")[0].text_content()
    name_dict = set_dict_key_value(consensual_estimates_data, name, {})
    LOG.debug(name)
    labels = chart_div.xpath("div[@class='yLabels']/p[@class='yLabel']")
    for l in labels:
        texts = l.text_content().split('|')
        set_dict_key_value(name_dict, texts[0], texts[1])
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

def get_stock_info_dict(connectionpool, stock):
    stock_info = {}

    infos = {'General-Information': parse_stock_general_information,
             'General-Profile': parse_stock_general_profile,
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

    stock_info['datetime'] = str(datetime.datetime.now())
    return stock_info

def get_stock_info_json(connectionpool, stock):
    return json.dumps(get_stock_info_dict(connectionpool, stock))


