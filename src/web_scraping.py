from logging import info, error, basicConfig, INFO
from web_scraping import IndexFearGreed
import transaction_handler
import requests

basicConfig(level=INFO, format='%(asctime)s - %(levelname)s - %(message)s')   
    
#index <= 25 : Extreme Fear | index <= 46 : Fear | index >=47 : Neutral | index >= 55 : Greed | index >= 76 : Extreme Greed
def get_index_fear_greed(url):
    """
    Get the latest data of the Fear and Greed Index.

    Parameters:
    - url (str): The URL to retrieve the Fear and Greed Index data.

    Returns:
    - tuple: A tuple containing the index values for the current day, yesterday, last week, and last month.
    """
    info(f'Function get_index_fear_greed')
    get_index_feargreed = requests.get(url)
    get_index_feargreed = get_index_feargreed.json()
    get_index_feargreed = get_index_feargreed
    array = []

    for item in get_index_feargreed['data']:
        value = int(item['value'])
        array.append(value)

    index_current = int(get_index_feargreed['data'][0]['value'])
    index_yesterday = int(get_index_feargreed['data'][1]['value'])
    array_last_month = array[:30]        
    array_len = len(array_last_month)
    index_last_week = int(sum(array_last_month)/array_len)
    array_last_week = array[:7]
    array_len = len(array_last_week)
    index_last_month = int(sum(array_last_week)/array_len)
    index_coinmarketcap = int(IndexFearGreed(find='span').get_index_fear_greed_coinmarketcap())
    
    if index_coinmarketcap != -1:
        index_current = int((index_coinmarketcap + index_current) / 2)
    
    return index_current, index_yesterday, index_last_week, index_last_month

def get_statistic_global(url):
    """
    Get crypto market insights.

    Parameters:
    - url (str): The URL to retrieve global market information.

    Returns:
    - tuple: a tuple containing the total market value, 24-hour trading volume and Bitcoin dominance.
    """
    info(f'Function get_statistic_global')
    statistic_global = requests.get(url)
    statistic_global = statistic_global.json()
    total = statistic_global['total_market_cap_usd']
    volume = statistic_global['total_24h_volume_usd']
    dominance = statistic_global['bitcoin_percentage_of_market_cap']
    return total, volume, dominance

def get_statistic_token(symbol, url, timestamp):
    """
    Get specific token statistics from a given URL based on the provided symbol.

    Parameters:
    - symbol (str): The symbol of the token (e.g., 'BTC', 'ETH').
    - url (str): The URL to retrieve token statistics.

    Returns:
    - tuple: A tuple containing the 24-hour trading volume, market cap, and percentage changes in 1h, 24h, and 7d.
    """
    info(f'Function get_statistic_token')
    statistic_token = requests.get(url)
    statistic_token =  statistic_token.json() 
    for i in statistic_token:
        i['id'] = i['symbol']   
    try:
        statistic_token = [i for i in statistic_token if i['id'] == symbol]
        volume = float(statistic_token[0]['24h_volume_usd'])
        marketcap = float(statistic_token[0]['market_cap_usd'])
        percent_1h = float(statistic_token[0]['percent_change_1h'])
        percent_24h = float(statistic_token[0]['percent_change_24h'])
        percent_7d = float(statistic_token[0]['percent_change_7d'])
        return volume, marketcap, percent_1h, percent_24h, percent_7d    
    except:
        try:
            #Abstract into a later function
            candlestick_list = transaction_handler.get_candlestick_chart_data('XRD', timestamp, 2, '1h')
            percent_1h = ((candlestick_list['data'][0][4]/candlestick_list['data'][-1][4])-1)*100

            candlestick_list = transaction_handler.get_candlestick_chart_data('XRD', timestamp, 2, '1d')
            percent_24h = ((candlestick_list['data'][0][4]/candlestick_list['data'][-1][4])-1)*100
            volume = candlestick_list['data'][0][5]
            marketcap = (candlestick_list['data'][0][5])*20
            
            candlestick_list = transaction_handler.get_candlestick_chart_data('XRD', timestamp, 7, '1d')
            percent_7d = ((candlestick_list['data'][0][4]/candlestick_list['data'][-1][4])-1)*100
            return volume, marketcap, percent_1h, percent_24h, percent_7d
        except:
            volume = marketcap = percent_1h = percent_24h = percent_7d = 1e-7
            return volume, marketcap, percent_1h, percent_24h, percent_7d