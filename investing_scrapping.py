import urllib3
import re
from lxml import html
import json
import unicodedata

BASE_URL = "https://br.investing.com/equities"
STOCK = 'all-amer-lat-on-nm'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
http_connection_pool = urllib3.PoolManager()

req = http_connection_pool.request(method='GET', url='https://br.investing.com/equities/StocksFilter',
                                   fields={'index_id': '17920', 'tabletype': 'technical', 'smlID': '602',
                                           'noconstruct': '1'},
                                   headers={'User-Agent': USER_AGENT})
html_tree = html.fromstring(req.data.decode('utf-8'))

column_indexes = {}
col_name_field = 'data-col-name'
data = html_tree.xpath('//table[@id="marketsTechnical"]/thead/tr/th')
index = 0
for th in data:
    if col_name_field in th.attrib.keys():
        column_indexes[th.attrib[col_name_field]] = index
    index += 1

data = html_tree.xpath('//table[@id="marketsTechnical"]/tbody/tr')
for tr in data:
    print("##########################################################")
    for field in column_indexes.keys():
        print("%s=%s" % (field, tr.getchildren()[column_indexes[field]].text_content().strip()))


#######################################################################################################################
#######################################################################################################################
def normalize_and_encode(str):
    return unicodedata.normalize('NFKD', str).encode('ascii','ignore')

def generate_html_tree(connectionpool, url, httpmethod='GET', headers={'User-Agent': USER_AGENT}, fields=None):
    req = connectionpool.request(method=httpmethod, url=url, headers=headers, fields=fields)
    return html.fromstring(normalize_and_encode(req.data.decode('utf-8')))


#######################################################################################################################
# Geral/Informação
def parse_stock_general_information(connectionpool, stock):
    general_information_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s" % (BASE_URL, stock))
    data = html_tree.xpath('//div[@class="instrumentHead"]/h1[@itemprop="name"]')[0].text_content()
    stockcode = re.search("\((.*)\)", data).group(1)
    general_information_data['code'] = stockcode
    print("%s=%s" % ("code", stockcode))

    data = html_tree.xpath(
        '//div[@class="clear overviewDataTable overviewDataTableWithTooltip"]//div[@class="inlineblock"] | //div[@class="first inlineblock"]')
    for div in data:
        general_information_data[div.getchildren()[0].text_content().strip()] = div.getchildren()[1].text_content().strip()

    return general_information_data


#######################################################################################################################
# Geral/Perfil
def parse_stock_general_information(connectionpool, stock):
    general_profile_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s-company-profile" % (BASE_URL, stock))
    data = html_tree.xpath('//div[@class="companyProfileHeader"]/div')
    for div in data:
        prop = div.text
        value = div.text_content().replace(prop, '')
        general_profile_data[prop] = value
        print("%s=%s" % (prop, value))

    return general_profile_data


####Finanças/Finanças
def parse_stock_finance_finance(connectionpool, stock):
    finance_finance_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url="%s/%s-financial-summary" % (BASE_URL, stock))
    summaries = html_tree.xpath('//div[@id="rsdiv"]/div[@class="companySummaryIncomeStatement"]')
    for summary in summaries:
        title = summary.xpath('h3/a')[0].text_content().strip()
        title = " ".join(title.split()[1:])
        finance_finance_data[title] = {}
        print(title)

        data = summary.xpath('div[@class="info float_lang_base_2"]/div[@class="infoLine"]')
        for div in data:
            spans = div.getchildren()
            item, value, complement = (spans[0].text_content().strip(), spans[2].text_content().strip(), spans[1].text_content().strip())
            print("\t%s=%s\t%s" % (item, value, complement))
            finance_finance_data[title][item] = (value, complement)

        data = summary.xpath('table[@class="genTbl openTbl companyFinancialSummaryTbl"]/thead//th')
        encerramentos_exercicios = [d.text_content().strip() for d in data[1:]]
        data = summary.xpath('table[@class="genTbl openTbl companyFinancialSummaryTbl"]/tbody/tr')
        for tr in data:
            trchildrens = tr.getchildren()
            item = trchildrens[0].text_content().strip()
            finance_finance_data[title][item] = {}
            print('\t' + item)
            for e, v in zip(encerramentos_exercicios, tr.getchildren()[1:]):
                finance_finance_data[title][item][e] = v.text_content().strip()
                print("\t\t%s=%s" % (e, v.text_content().strip()))
    return finance_finance_data


####Finanças/Demonstrações
def finance_demonstrations(connectionpool, stock):
    finance_demonstrations_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-income-statement' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content().strip()
        finance_demonstrations_data[item_name] = {}
        print(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            finance_demonstrations_data[item_name][e] = v.text_content().strip()
            print("\tExercicio=%s:\t%s" % (e, v.text_content().strip()))
    return finance_demonstrations_data


####Finanças/Balanço Patrimonial
def finance_balances(connectionpool, stock):
    finance_balances_data = {}

    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-balance-sheet' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content().strip()
        finance_balances_data[item_name] = {}
        print(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            finance_balances_data[item_name][e] = v.text_content().strip()
            print("\tExercicio=%s:\t%s" % (e, v.text_content().strip()))
    return finance_balances_data


####Finanças/Fluxo de Caixa
def finance_cash_flow(connectionpool, stock):
    finance_cashflow_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-cash-flow' % (BASE_URL, stock))
    data = html_tree.xpath('//div[@id="rrtable"]/table//tr[@id="header_row"]/th')
    encerramentos_exercicios = ["%s/%s" % (children[1].text_content().strip(), children[0].text_content().strip()) for
                                children in data[1:]]
    data = html_tree.xpath('//div[@id="rrtable"]/table//td/span[@class=" bold"]/../..')
    for item in data:
        item_name = item.getchildren()[0].text_content().strip()
        finance_cashflow_data[item_name] = {}
        print(item_name)
        for e, v in zip(encerramentos_exercicios, item.getchildren()[1:]):
            finance_cashflow_data[item_name][e] = v.text_content().strip()
            print("\tExercicio=%s:\t%s" % (e, v.text_content().strip()))
    return finance_cashflow_data


####Finanças/Indicadores
def finance_indicators(connectionpool, stock):
    finance_indicators_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-ratios' % (BASE_URL, stock))
    escopo_indicadores = [x.text_content().strip() for x in html_tree.xpath('//table[@id="rrTable"]/thead/tr/th')[1:]]
    indicadores = html_tree.xpath('//table[@id="rrTable"]/tbody/tr[@id="childTr"]/td/div/table/tbody/tr/td/span/../..')
    for indicador in indicadores:
        indicator_name = indicador.getchildren()[0].text_content().strip()
        finance_indicators_data[indicator_name] = {}
        print(indicator_name)
        for e, i in zip(escopo_indicadores, indicador.getchildren()[1:]):
            finance_indicators_data[indicator_name][e] = i.text_content().strip()
            print("\t%s=%s" % (e, i.text_content().strip()))
    return finance_indicators_data


####Finanças/Lucros
def finance_profits(connectionpool, stock):
    finance_profits_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-earnings' % (BASE_URL, stock))
    columns = [col.text_content().replace("/", "").strip() for col in
               html_tree.xpath('//table[@class="genTbl openTbl ecoCalTbl earnings earningsPageTbl"]/thead/tr/th[text()]')]
    earningshistory = html_tree.xpath('//tr[@name="instrumentEarningsHistory"]')
    for history in earningshistory:
        exercise_date = history.getchildren()[1].text_content().strip()
        finance_profits_data[exercise_date] = {}
        print("Exercício=" + exercise_date)
        for c, h in zip(columns, history.getchildren()):
            value = h.text_content().replace("/", "").strip() if h.text_content().startswith("/") else h.text_content().strip()
            finance_profits_data[exercise_date][c] = value
            print("\t%s=%s" % (c, value))
    return finance_profits_data

####Técnica/Análise Técnica
def technical_technical_analysis(connectionpool, stock):
    technical_analysis_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-technical' % (BASE_URL, stock))
    periods = [(p.text_content(), p.get('pairid'), p.get('data-period')) for p in
               html_tree.xpath('//div[@id="technicalstudiesSubTabs"]/ul/li')]
    for period in periods:
        period_name = period[0]
        technical_analysis_data[period_name] = {}
        print(period_name)
        html_tree = generate_html_tree(connectionpool=http_connection_pool, httpmethod='POST',
                                       url='https://br.investing.com/instruments/Service/GetTechincalData',
                                       headers={'User-Agent': USER_AGENT, 'X-Requested-With': 'XMLHttpRequest'},
                                       fields={'pairID': period[1], 'period': period[2]})

        tech_summary_div = html_tree.xpath('//div[@id="techStudiesInnerWrap"]')[0]

        summary = tech_summary_div.xpath('//div[@class="summary"]/span[1]')[0].text_content()
        technical_analysis_data[period_name]['Resumo']={}
        technical_analysis_data[period_name]['Resumo']['Resumo']=summary
        print('\tResumo=%s' % (summary))

        for summary_table_line in tech_summary_div.xpath('div[@class="summaryTableLine"]'):
            name, value = (summary_table_line[0].text_content().replace(':', ''), summary_table_line[1].text_content())
            technical_analysis_data[period_name]['Resumo'][name]={}

            technical_analysis_data[period_name]['Resumo'][name]['Resumo']=value
            print("\t\t%s=%s" % (name, value))

            moving_avg_summ = summary_table_line[2].getchildren()
            x, y = (moving_avg_summ[0].text_content(), moving_avg_summ[1].text_content().replace('(', '').replace(')', ''))
            technical_analysis_data[period_name]['Resumo'][name][x]=y
            print("\t\t\t%s=%s" % (x, y))

            tech_indicators_sum = summary_table_line[3].getchildren()
            x, y = (tech_indicators_sum[0].text_content(), tech_indicators_sum[1].text_content().replace('(', '').replace(')', ''))
            technical_analysis_data[period_name]['Resumo'][name][x] = y
            print("\t\t\t%s=%s" % (x, y))

        technical_analysis_data[period_name]['Pontos de Pivot'] = {}
        print("\tPontos de Pivot")
        pivot_points_table = html_tree.xpath('//table[@id="curr_table"]')[0]
        headers = [x.text_content().strip() for x in pivot_points_table.xpath('thead/tr/th')[1:]]
        pivot_indicators = pivot_points_table.xpath('tbody/tr')
        for indicator in pivot_indicators:
            indicator_name = indicator.getchildren()[0].text_content().strip()
            technical_analysis_data[period_name]['Pontos de Pivot'][indicator_name]={}
            print("\t\t%s" % (indicator_name))
            for h, i in zip(headers, indicator.getchildren()[1:]):
                technical_analysis_data[period_name]['Pontos de Pivot'][indicator_name][h]=i.text_content().strip()
                print("\t\t\t%s=%s" % (h, i.text_content()))

        technical_analysis_data[period_name]['Indicadores Técnicos']={}
        print("\tIndicadores Técnicos")
        tech_indicators_table = html_tree.xpath('//table[@id="curr_table"]')[1]
        headers = [x.text_content().strip() for x in tech_indicators_table.xpath('thead/tr/th')[1:]]
        tech_indicators = tech_indicators_table.xpath('tbody/tr')
        for indicator in tech_indicators[:-1]:
            indicator_name = indicator.getchildren()[0].text_content()
            technical_analysis_data[period_name]['Indicadores Técnicos'][indicator_name]={}
            print("\t\t%s" % (indicator_name))
            for h, i in zip(headers, indicator.getchildren()[1:]):
                technical_analysis_data[period_name]['Indicadores Técnicos'][indicator_name][h]=i.text_content().strip()
                print("\t\t\t%s=%s" % (h, i.text_content().strip()))
        technical_analysis_data[period_name]['Indicadores Técnicos']['Total'] = {}
        print("\t\tTotal")
        for p in tech_indicators_table.xpath('tbody/tr[last()]/td/p')[:-1]:
            p_children = p.getchildren()
            x, y = p_children[0].text_content().strip().replace(':', ''), p_children[1].text_content().strip()
            technical_analysis_data[period_name]['Indicadores Técnicos']['Total'][x]=y
            print("\t\t\t%s=%s" % (x, y))
        x = tech_indicators_table.xpath('tbody/tr[last()]/td/p[last()]/span')[0].text_content().strip()
        technical_analysis_data[period_name]['Indicadores Técnicos']['Total']['Resumo']=x
        print("\t\t\tResumo=%s" % (x))

        technical_analysis_data[period_name]['Médias Móveis'] = {}
        print("\tMédias Móveis")
        moving_avg_table = html_tree.xpath('//table[@id="curr_table"]')[2]
        headers = [x.text_content().strip() for x in moving_avg_table.xpath('thead/tr/th')[1:]]
        moving_avgs = moving_avg_table.xpath('tbody/tr')
        for mavg in moving_avgs[:-1]:
            mavgname = mavg.getchildren()[0].text_content().strip()
            technical_analysis_data[period_name]['Médias Móveis'][mavgname]={}
            print("\t\t%s" % (mavgname))
            for h, v in zip(headers, mavg.getchildren()[1:]):
                technical_analysis_data[period_name]['Médias Móveis'][mavgname][h]={}
                print("\t\t\t%s" % (h))

                value = v.xpath('span/..')[0].text.strip()
                technical_analysis_data[period_name]['Médias Móveis'][mavgname][h]['Valor']=value
                print("\t\t\t\tValor=%s" % (value))

                action = v.xpath('span')[0].text.strip()
                technical_analysis_data[period_name]['Médias Móveis'][mavgname][h][
                    'Ação'] = action
                print("\t\t\t\tAção=%s" % (action))
        technical_analysis_data[period_name]['Médias Móveis']['Total']={}
        print("\t\tTotal")
        for p in moving_avg_table.xpath('tbody/tr[last()]/td/p')[:-1]:
            p_children = p.getchildren()
            x, y = (p_children[0].text_content().strip().replace(':', ''), p_children[1].text_content().strip())
            technical_analysis_data[period_name]['Médias Móveis']['Total'][x]=y
            print("\t\t\t%s=%s" % (x, y))
        y = tech_indicators_table.xpath('tbody/tr[last()]/td/p[last()]/span')[0].text_content().strip()
        technical_analysis_data[period_name]['Médias Móveis']['Total']['Resumo']=y
        print("\t\t\tResumo=%s" % (y))

    return technical_analysis_data

####Técnica/Padrão de Candlestick
def technical_candlestick_pattern(connectionpool, stock):
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
        print(name)

        x, y = headers[0], values[0].get('title')
        current_map[x] = y
        print("\t%s=%s" % (x, y))

        x, y = headers[1], values[2].text_content()
        current_map[x] = y
        print("\t%s=%s" % (x, y))

        x, y = headers[2], values[3].get('title')
        current_map[x] = y
        print("\t%s=%s" % (x, y))

        x, y = headers[3], values[4].text_content()
        current_map[x] = y
        print("\t%s=%s" % (x, y))

        x, y = headers[4], values[5].text_content() if len(values) == 6 else ""
        current_map[x] = y
        print("\t%s=%s" % (x, y))
    return tecnical_candlestick_pattern_data

####Técnica/Estimativas Consensuais
def consensual_estimates(connectionpool, stock):
    consensual_estimates_data = {}
    html_tree = generate_html_tree(connectionpool=connectionpool, url='%s/%s-consensus-estimates' % (BASE_URL, stock))
    chart_div = html_tree.xpath("//div[@class='graphChart']")[0]
    name = chart_div.xpath("p[@class='chartSmalltitle']")[0].text_content().strip()
    consensual_estimates_data[name]={}
    print(name)
    labels = chart_div.xpath("div[@class='yLabels']/p[@class='yLabel']")
    for l in labels:
        texts = l.text_content().split('|')
        consensual_estimates_data[name][texts[0].strip()] = texts[1].strip()
        print("\t%s=%s" % (texts[0].strip(), texts[1].strip()))
    return consensual_estimates_data

def get_stock_info_json(connectionpool, stock):
    stock_info = {
        'General-Information': parse_stock_general_information(connectionpool, stock),
        'Finance-Finance':parse_stock_finance_finance(connectionpool, stock),
        'Finance-Demonstrations': finance_demonstrations(connectionpool, stock),
        'Finance-Balances':finance_balances(connectionpool, stock),
        'Finance-CashFlow':finance_cash_flow(connectionpool, stock),
        'Finance-Indicators':finance_indicators(connectionpool, stock),
        'Finance-Profits':finance_profits(connectionpool, stock),
        'Technical-TechnicalAnalysis':technical_technical_analysis(connectionpool, stock),
        'Technical-CandlestickPattern':technical_candlestick_pattern(connectionpool, stock),
        'Technical-ConsensualEstimates':consensual_estimates(connectionpool, stock)
    }
    return json.dumps(stock_info)