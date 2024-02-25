from datetime import datetime, timedelta
from hashlib import sha256
import numpy as np
import configparser
import boto3
import telepot
import requests
import hmac
import time
import pytz
import json
import re

class Config:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_api_url_bingx(self):
        return self.config['API']['APIURL_BINGX']
    
    def get_api_key_bingx(self):
        return self.config['API']['APIKEY_BINGX']
    
    def get_api_secretkey_bingx(self):
        return self.config['API']['SECRETKEY_BINGX']
    
    def get_address_bingx(self):
        return self.config['BLOCKCHAIN']['ADDRESS_BINGX_ETH']

    def get_api_key_telegram(self):
        return self.config['TELEGRAM']['BOTKEY']
    
    def get_api_chatkey_telegram(self):
        return self.config['TELEGRAM']['CHATKEY']
    
    def get_statistic_token(self):
        return self.config['API']['APIURL_TOKEN_ALTERNATIVE']

    def get_statistic_global(self):
        return self.config['API']['APIURL_GLOBAL_ALTERNATIVE']

    def get_index_feargreed(self):
        return self.config['API']['APIURL_INDEX_ALTERNATIVE']

    def get_token_symbol(self):
        return list(self.config['TOKEN'].values())
    
    def get_token_address(self):
        return list(self.config['BLOCKCHAIN_ADDRESS'].values())
    
    def get_blockchain_network(self):
        return list(self.config['BLOCKCHAIN_NETWORK'].values())

    def get_tag_wallet(self):
        return list(self.config['TAG'].values())
    
    def get_current_time(self):
        timezone_summer = pytz.timezone('America/Cayman')
        current_time = datetime.now(timezone_summer)
        current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        return current_time

    def get_bucket_name(self):
        return self.config['AWS']['BUCKET_BOT_DCA_ITCHY']
    
config_file = 'config.ini'
config = Config(config_file)
statistic_token = config.get_statistic_token()
statistic_global = config.get_statistic_global()
get_index_feargreed = config.get_index_feargreed()
APIURL_BINGX = config.get_api_url_bingx()
APIKEY_BINGX = config.get_api_key_bingx()
SECRETKEY_BINGX = config.get_api_secretkey_bingx()
BOTKEY = config.get_api_key_telegram()
CHATKEY = config.get_api_chatkey_telegram()
ADDRESS_BINGX_ETH = config.get_address_bingx()
BOTKEY = telepot.Bot(BOTKEY)
BUCKET_BOT_DCA_ITCHY = config.get_bucket_name()
token_symbol = config.get_token_symbol()
network_blockchain = config.get_blockchain_network()
address_tag = config.get_tag_wallet()
address_destination = config.get_token_address()
current_time = config.get_current_time()
re_default = r'[^a-zA-Z0-9\s]'

#handler function is a function that deals with specific events or requests in a program
def handler():
    """
    Handler function that processes events or requests for multiple tokens.

    Returns:
    - dict: A dictionary containing a simple status code.
    """
    for i in range(len(token_symbol)): #enable this loop when it becomes possible to implement the purchase of more than 1 token
        qty_token = get_balance(token_symbol[i], current_time)
        price_low, price_current, price_last = get_price(token_symbol[i], current_time)
        if qty_token is not None:
            check_balance_withdraw(round(qty_token * price_current,2), qty_token, token_symbol[i], network_blockchain[i], address_destination[i], address_tag[i], current_time)
        else: 
            bot_telegram('❌Alert\\!\n\nAPI error on '+current_time.replace('-', '\\-')
                +' \\(GMT\\-5\\)\\.\n\nFunction failure: qty\\_token is null')
    return {
        'statusCode': 200,
    }
 
#get sign request secretkey to generate a signature
def get_sign(api_secret, payload):
    """
    Generate a signature for authenticating an API request.

    Parameters:
    - api_secret (str): API secret key.
    - payload (str): Request data to be signed.

    Returns:
    - str: Generated signature as a hexadecimal string.
    """
    signature = hmac.new(api_secret.encode('utf-8'), payload.encode('utf-8'), digestmod=sha256).hexdigest()
    return signature

#single request api call
def send_request(method, path, urlpa, payload):
    """
    Make a call to the BingX API.

    Parameters:
    - method (str): HTTP method of the request (e.g., 'GET', 'POST').
    - path (str): API endpoint path.
    - urlpa (str): URL parameters.
    - payload (str): Request data.

    Returns:
    - str: Content of the API response.
    """
    url = '%s%s?%s&signature=%s' % (APIURL_BINGX, path, urlpa, get_sign(SECRETKEY_BINGX, urlpa))
    headers = {
        'X-BX-APIKEY': APIKEY_BINGX,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def praseParam(params_map):
    """
    Encapsulate parameters in a specific format for an API request.

    Parameters:
    - params_map (dict): Dictionary containing the request parameters.

    Returns:
    - str: Formatted string of parameters with timestamp added.
    """
    sortedKeys = sorted(params_map)
    params_str = '&'.join(['%s=%s' % (x, params_map[x]) for x in sortedKeys])
    return params_str+'&timestamp='+str(int(time.time() * 1000))

def get_balance(symbol, timestamp):
    """
    Get the balance of a specific cryptocurrency symbol from the spot trading account.

    Parameters:
    - symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
    - timestamp (str): Timestamp used for error logging.

    Returns:
    - float: The balance of the specified cryptocurrency symbol.
    - str: If an error occurs, return the error message.
    """
    payload = {}
    path = '/openApi/spot/v1/account/balance'
    method = 'GET'
    params_map = {
    'recvWindow': 0
    }
    params_str = praseParam(params_map)
    json_data = json.loads(send_request(method, path, params_str, payload))

    if 'data' in json_data:    
        for balance in json_data['data']['balances']:
            if balance['asset'] == symbol:
                amount = round(float(balance['free']),8)
                break
        return amount
    else: 
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: get\\_balance\n\nError: '+error)
        return error

def request_withdraw(symbol, network, address, addressTag, amount, timestamp):
    """
    Initiate a withdrawal request for a specific cryptocurrency.

    Parameters:
    - symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
    - network (str): The network for the withdrawal (e.g., 'BTC', 'ERC20').
    - address (str): The destination address for the withdrawal.
    - addressTag (str): Address tag or memo for certain cryptocurrencies.
    - amount (float): The amount of cryptocurrency to withdraw.
    - timestamp (str): Timestamp used for error logging.

    Returns:
    - int: If successful, returns the withdrawal request ID.
    - str: If an error occurs, returns the error message.
    """
    payload = {}
    path = '/openApi/wallets/v1/capital/withdraw/apply'
    method = 'POST'
    params_map = {
    'coin': symbol,
    'network': network,
    'address': address,
    'addressTag': addressTag,
    'amount': amount,
    'walletType': 1
    }
    params_str = praseParam(params_map)
    json_data = json.loads(send_request(method, path, params_str, payload))

    if 'data' in json_data:  
        result = json_data['data']['id']
        bot_telegram('✅Withdrawal Successful\n\nYou have sucessfully withdrawn '+str(amount).replace('.', '\\.')
            +' '+symbol+' on '+timestamp.replace('-', '\\-')+' \\(GMT\\-5\\)\\.\n\nDestination address:\n\n`'
            +address+'`\n\nTransaction ID:\n`'+str(result)+'`')
        return result
    else:
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: request\\_withdraw\n\nError: '+error)
        return error
    
def get_withdrawfee(symbol,network,timestamp):
    """
    Retrieve the withdrawal fee for a specific cryptocurrency and network.

    Parameters:
    - symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
    - network (str): The network for the withdrawal (e.g., 'BTC', 'ERC20').
    - timestamp (str): Timestamp used for error logging.

    Returns:
    - float: The withdrawal fee for the specified cryptocurrency and network.
    - str: If an error occurs, returns the error message.
    """
    network_fee = float(0.0)
    network = network.upper()
    payload = {}
    path = '/openApi/wallets/v1/capital/config/getall'
    method = "GET"
    params_map = {
    "recvWindow": 0
    }
    params_str = praseParam(params_map)
    json_data = json.loads(send_request(method, path, params_str, payload))
    
    if 'data' in json_data:  
      json_data = json_data['data']
      for i in json_data:
        network_list = i.get("networkList", [])
        for fee  in network_list:
          if fee.get("name") == symbol and fee.get("network") == network:
            network_fee = float(fee['withdrawFee'])
            return network_fee
    else: 
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                +' \\(GMT\\-5\\)\\.\n\nFunction failure: get\\_withdrawfee\n\nError: '+error)
        return error

def place_order(symbol, quantity, timestamp, index_current, index_class, dominance_btc_global, percent_1h_token, percent_24h_token,percent_7d_token, rsi_value, intensity):
    """
    Place a market buy order for a specified cryptocurrency symbol.

    Parameters:
    - symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
    - quantity (float): The quantity of the cryptocurrency to buy.
    - timestamp (str): Timestamp used for logging and notification.
    - index_current (float): Number Fear and Greed Index.
    - index_class (str): Classification Fear and Greed Index.
    - dominance_btc_global (float): BTC dominance in the global market.
    - percent_1h_token (float): 1-hour price change percentage for the token.
    - percent_24h_token (float): 24-hour price change percentage for the token.
    - percent_7d_token (float): 7-day price change percentage for the token.
    - rsi_value (float): RSI (Relative Strength Index) value.
    - intensity (float): Buy hand intensity value.

    Returns:
    - dict: If successful, returns a dictionary containing order details and market information.
    - dict: If an error occurs, returns a dictionary with the 'statusCode' key set to 500.
    """
    payload = {}
    path = '/openApi/spot/v1/trade/order'
    method = 'POST'
    params_map = {
    'symbol': symbol+'-USDT',
    'side': 'BUY', #BUY/SELL
    'type': 'MARKET', #MARKET/LIMIT
    'timeInForce': 'POC', #IOC = immediate-or-cancel , POC = process-or-cancel
    'quoteOrderQty': quantity,
    'recvWindow': 0
    }
    params_str = praseParam(params_map)
    json_data = json.loads(send_request(method, path, params_str, payload))
    if 'data' in json_data:
        orderId = json_data['data']['orderId']
        priceOrder = round(float(json_data['data']['price']),3)
        qty = float(json_data['data']['executedQty'])
        status = str(json_data['data']['status']).lower()
        total = round(qty*priceOrder,3)
        flag = '✅' if status != 'canceled' else '❌'
        bot_telegram(flag+'Buy order '+status+'\n\nOrder ID: `'
                     +str(orderId)+'`\nDate: '+timestamp.replace('-', '\\-')+' \\(GMT\\-5\\)\\\nToken: '
                     +symbol+'\nPrice: \\$'+str(priceOrder).replace('.', '\\.')+'\nAmount: '
                     +str(qty).replace('.', '\\.')+'\nTotal: \\$'+str(total).replace('.', '\\.')+'\n\n📈Volatility in the Market\n\nIndex: '
                     +str(index_current).replace('.', '\\.')+' \\('+index_class+'\\)'
                     +'\nIntensity: '+str(round(intensity,2)).replace('.', '\\.').replace('-', '\\-')
                     +'\nRSI: '+str(round(rsi_value,2)).replace('.', '\\.')+'%'
                     +'\nBTC Dominance: '+str(round(dominance_btc_global,2)).replace('.', '\\.')+'%'
                     +'\n1H Units: '+str(round(percent_1h_token,2)).replace('.', '\\.').replace('-', '\\-')+'%\n24H Units: '
                     +str(round(percent_24h_token,2)).replace('.', '\\.').replace('-', '\\-')+'%\n7D Units: '
                     +str(round(percent_7d_token,2)).replace('.', '\\.').replace('-', '\\-')+'%')

        #register order in csv
        bucket_name = BUCKET_BOT_DCA_ITCHY
        token_lower = symbol.lower()
        token_lower = token_lower if 'wbtc' != symbol else 'btc'
        file_name = 'token/'+token_lower+'.csv'
        s3 = boto3.client('s3')

        try:
            response = s3.get_object(Bucket=bucket_name, Key=file_name)
            csv_data = response['Body'].read().decode('utf-8')

        except s3.exceptions.NoSuchKey:
            csv_data = 'symbol,quantity,price,timestamp,index_current,index_class,dominance_btc_global,percent_1h_token,percent_24h_token,percent_7d_token,rsi_value,intensity\n'
            s3.put_object(Bucket=bucket_name, Key=file_name, Body=csv_data)

        except Exception as e:
            
            return {
                'statusCode': 500,
            }
        
        csv_data = csv_data+(symbol+','+str(qty)+','+str(priceOrder)+','+str(timestamp)+','
                    +str(index_current)+','+str(index_class)+','
                    +str(dominance_btc_global)+','+str(percent_1h_token)+','
                    +str(percent_24h_token)+','+str(percent_7d_token)+','
                    +str(rsi_value)+','+str(intensity)+'\n')                   
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=csv_data)
        return orderId, priceOrder, qty, status 
     
    else:
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: place\\_order\n\nError: '+error)
        return error

def cancel_order(symbol, orderId, timestamp):
    """
    Cancel a specific order for a given cryptocurrency symbol.

    Parameters:
    - symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
    - orderId (int): The ID of the order to be canceled.
    - timestamp (str): Timestamp used for error logging and notification.

    Returns:
    - int: If successful, returns the client order ID of the canceled order.
    - str: If an error occurs, returns the error message.
    """
    payload = {}
    path = '/openApi/spot/v1/trade/cancel'
    method = 'POST'
    params_map = {
    'symbol': symbol +'-USDT',
    'orderId': orderId,
    'recvWindow': 0
    }
    params_str = praseParam(params_map)
    json_data = json.loads(send_request(method, path, params_str, payload))
    
    if 'data' in json_data:
        client_order_id = json_data['data']['client_order_id']
        return client_order_id
    else: 
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: cancel\\_order\n\nError: '+error)
        return error

def get_price(symbol, timestamp):
    """
    Retrieve current price information for a given cryptocurrency symbol.

    Parameters:
    - symbol (str): The symbol of the cryptocurrency (e.g. 'BTC', 'ETH').
    - timestamp (str): Timestamp used for recording and error notification.

    Returns:
    - tuple: If successful, returns a tuple containing the 24-hour minimum price, current price, and price changes.
    - str: If an error occurs, returns the error message.
    """
    payload = {}
    path = '/openApi/spot/v1/ticker/24hr'
    method = 'GET'
    params_map = {
    'symbol': symbol +'-USDT'
    }
    params_str = praseParam(params_map)
    json_data = json.loads(send_request(method, path, params_str, payload))

    if 'data' in json_data: 
        low = round(json_data['data'][0]['lowPrice'],4)
        current = round(json_data['data'][0]['lastPrice'],4)
        changes = round(json_data['data'][0]['openPrice'],4)
        return low, current, changes
    else:
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: price\\_current\n\nError: '+error)
        return error

def get_rsi(symbol, timestamp):
    """
    Calculate the Relative Strength Index (RSI) for a given cryptocurrency symbol over a 14-day period.

    Parameters:
    - symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
    - timestamp (str): Timestamp used for error logging and notification.

    Returns:
    - float: If successful, returns the calculated RSI value.
    - str: If an error occurs, returns the error message.
    """
    current_datetime = datetime.now()
    resultant_date = current_datetime - timedelta(days=14)
    desired_time = datetime(resultant_date.year, resultant_date.month, resultant_date.day, 15, 59, 59)
    start_epoch_timestamp = int(str(int(desired_time.timestamp()))+'000')
    end_epoch_timestamp = int(str(int(time.time()))+'000')
    payload = {}
    path = '/openApi/spot/v1/market/kline'
    method = 'GET'
    params_map = {
    'symbol': symbol +'-USDT',
    'interval': '1d',
    'startTime': start_epoch_timestamp,
    'endTime': end_epoch_timestamp,
    'limit' : 14
    }  
    params_str = praseParam(params_map)
    json_data = json.loads(send_request(method, path, params_str, payload))
    
    if 'data' in json_data:
      opening = []
      closing = []

      for i in json_data['data']:
          open = float(i[1])
          closed = float(i[4])
          opening.append(open)
          closing.append(closed)
                 
      daily_change = [closing[i] - opening[i] for i in range(len(opening))]
      positive_change = [max(0, change) for change in daily_change]
      negative_change = [-min(0, change) for change in daily_change]
      period = 14
      moving_average_gains = [np.mean(positive_change[:period])]
      moving_average_losses = [np.mean(negative_change[:period])]

      for i in range(period, len(daily_change)):
          gain = positive_change[i]
          loss = negative_change[i]
          moving_average_gains.append(((period - 1) * moving_average_gains[-1] + gain) / period)
          moving_average_losses.append(((period - 1) * moving_average_losses[-1] + loss) / period)
      rs = [moving_average_gains[i] / moving_average_losses[i] for i in range(len(moving_average_gains))]
      rsi = [100 - (100 / (1 + rs_value)) for rs_value in rs]
      rsi = rsi[0]
      return rsi  
    else:
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('✅Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: get\\_rsi\n\nError: '+error)
        return error

def bot_telegram(msg_text):
    """
    Send a message to a specified Telegram chat using the provided message text.

    Parameters:
    - msg_text (str): The text of the message to be sent.

    Returns:
    - None
    """
    BOTKEY.sendMessage(CHATKEY, msg_text, parse_mode='MarkdownV2')

#index <= 25 : Extreme Fear | index <= 46 : Fear | index >=47 : Neutral | index >= 55 : Greed | index >= 76 : Extreme Greed
def get_index_fear_greed(url):
    """
    Get the latest data of the Fear and Greed Index.

    Parameters:
    - url (str): The URL to retrieve the Fear and Greed Index data.

    Returns:
    - tuple: A tuple containing the index values for the current day, yesterday, last week, and last month.
    """
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
    return index_current, index_yesterday, index_last_week, index_last_month

def get_statistic_global(url):
    """
      Get crypto market insights.

      Parameters:
      - url (str): The URL to retrieve global market information.

      Returns:
      - tuple: a tuple containing the total market value, 24-hour trading volume and Bitcoin dominance.
      """
    statistic_global = requests.get(url)
    statistic_global = statistic_global.json()
    total = statistic_global['total_market_cap_usd']
    volume = statistic_global['total_24h_volume_usd']
    dominance = statistic_global['bitcoin_percentage_of_market_cap']
    return total, volume, dominance

def get_statistic_token(symbol, url):
    """
    Get specific token statistics from a given URL based on the provided symbol.

    Parameters:
    - symbol (str): The symbol of the token (e.g., 'BTC', 'ETH').
    - url (str): The URL to retrieve token statistics.

    Returns:
    - tuple: A tuple containing the 24-hour trading volume, market cap, and percentage changes in 1h, 24h, and 7d.
    """
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
        volume = marketcap = percent_1h = percent_24h = percent_7d = 1e-7
        return volume, marketcap, percent_1h, percent_24h, percent_7d
        
def check_balance_withdraw(balance, amount, symbol, network, address, tag, timestamp):  
    """
    Withdraw balance and check if there are USDT funds in the wallet.

    Parameters:
    - balance (float): The balance of the specified token.
    - amount (float): The amount to withdraw.
    - symbol (str): The symbol of the token (e.g., 'BTC', 'ETH').
    - network (str): The network for withdrawal (e.g., 'ETH', 'TRX').
    - address (str): The withdrawal address.
    - tag (str): The withdrawal tag.
    - timestamp (str): Timestamp used for error logging and notification.

    Returns:
    - None
    """
    usdt = get_balance('USDT', timestamp)
    time.sleep(0.100)
    value = 5
    if usdt < 5:
      bot_telegram('❌Alert\\!\n\nDCA not completed\n\nYour USDT balance is $'
                    +str(round(usdt,2)).replace('.', '\\.')+', please deposit to address: \n\n`'+ADDRESS_BINGX_ETH+'`')
    else:
        buy_dca(symbol,value,usdt,timestamp)    
    time.sleep(0.100)
    fee = get_withdrawfee(symbol,network,timestamp)   
    try:
        fee_percentage = fee / amount
    except:
        fee_percentage = 1
    if fee_percentage < 0.05 and amount >= 10:
        bot_telegram('⚠️Alert\\!\n\nMake the withdrawal\n\nYour '+symbol.replace('-', '\\-')+' balance is\nAmount: $'
                    +str(round(balance,2)).replace('.', '\\.')+'\nQty: '
                    +str(round(amount,4)).replace('.', '\\.')+'\nFee: '
                    +str(round(fee,4)).replace('.', '\\.')+'\nPercentage Fee: '
                    +str(round((fee / amount) * 100,2)).replace('.', '\\.')+'%')
    else:
        time.sleep(0.100)
    
def indicators(symbol):
    """
    Calculate a set of indicators for a given cryptocurrency token.

    Parameters:
    - symbol (str): The symbol of the token (e.g., 'BTC', 'ETH').

    Returns:
    - tuple: A tuple containing the calculated indicators for the token.
    """
    index_current, index_yesterday, index_last_week, index_last_month = get_index_fear_greed(get_index_feargreed)
    total_global, volume_global, dominance_btc_global = get_statistic_global(statistic_global)
    volume_24h_token, total_marketcap_token, percent_1h_token, percent_24h_token, percent_7d_token = get_statistic_token(symbol if 'WBTC' != symbol else 'BTC', statistic_token)
    rsi_value = get_rsi(symbol if 'WBTC' != symbol else 'BTC', current_time)
    array_index = [index_current, index_yesterday, index_last_week, index_last_month]
    trends = [((index_current - array_number) / array_number) * 100 for array_number in array_index]
    overview_trends = sum(trends)/len(trends)

    #index fear and greed
    if index_current <= 25:
        index_w = 1
        index_class = 'Extreme Fear'
    elif index_current <= 46:
        index_w = 0.7
        index_class = 'Fear'
    elif index_current >= 47 and index_current <= 54:
        index_w = 0.2
        index_class = 'Neutral'
    elif index_current >= 55 and index_current <= 75:
        index_w = -0.4
        index_class = 'Greed'
    elif index_current >= 76:
        index_w = -0.6
        index_class = 'Extreme Greed'
    else:
        index_w = 0

    if overview_trends < -5:
        index_v = 1
    elif overview_trends < -4:
        index_v = 0.7
    elif overview_trends < -3:
        index_v = 0.2
    elif overview_trends < 1:
        index_v = 0.01
    else:
        index_v = 0

    index_end = (index_v * 0.6 + index_w * 0.4) * 1.5

    #marketcap x volume daily
    volume_marketcap = (volume_global / total_global) * 100

    if volume_marketcap >= 10 or volume_marketcap <= -10:
        volume_w = 0
    elif 'BTC' in symbol and dominance_btc_global >= 50:
        volume_w = 0
    elif 'BTC' in symbol and dominance_btc_global < 50:
        volume_w = 1
    elif 'BTC' not in symbol and dominance_btc_global >= 50:
        volume_w = 1
    else:
        volume_w = 0
        
    volume_end = volume_w * 0.075

    #price changes
    volume_marketcap_token = (volume_24h_token / total_marketcap_token) * 100

    if volume_marketcap_token >= 10 and volume_marketcap_token <= -10:
        price_changes_w = 0
    elif percent_1h_token > 0 and percent_24h_token > 0 and percent_7d_token > 0:
        price_changes_w = -0.4
    elif percent_1h_token < 0 and percent_24h_token < 0 and percent_7d_token < 0:
        price_changes_w = 1
    elif percent_1h_token > 0 and percent_24h_token > 0:
        price_changes_w = -0.2
    elif percent_1h_token < 0 and percent_24h_token < 0:
        price_changes_w = 0.7
    else:
        price_changes_w = 0
  
    price_changes_end = price_changes_w * 0.375

    #rsi
    if rsi_value >= 70: 
        rsi_w = -0.7
    elif rsi_value >= 50: 
        rsi_w = 0.6
    elif rsi_value > 30 and rsi_value < 50: 
        rsi_w = 0.8
    elif rsi_value <= 30: 
        rsi_w = 1
    else:
        rsi_w = 0

    rsi_end = rsi_w * 1.05

    #resultant
    total_end = index_end + volume_end + price_changes_end + rsi_end

    return index_current, index_class, dominance_btc_global, percent_1h_token, percent_24h_token,percent_7d_token, rsi_value, total_end

#buy using dca by intensity
def buy_dca(symbol, quantity, usdt,timestamp):
    """
    Buy using Dollar-Cost Averaging (DCA) strategy by intensity.

    Parameters:
    - symbol (str): The symbol of the token (e.g., 'BTC', 'ETH').
    - quantity (float): The initial quantity to buy based on intensity.
    - usdt (float): The available USDT balance for the purchase.
    - timestamp (str): Timestamp used for order placement and logging.

    Returns:
    - tuple: A tuple containing the order ID, price, quantity, and status of the DCA purchase.
    """
    index_current, index_class, dominance_btc_global, percent_1h_token, percent_24h_token,percent_7d_token, rsi_value, total_end = indicators(symbol)
    quantity = quantity*total_end
    quantity = 5 if quantity < 5 else quantity
    quantity = usdt if quantity > usdt else quantity
    orderid, priceorder, qty, status = place_order(symbol, quantity, timestamp, index_current, index_class, dominance_btc_global, percent_1h_token, percent_24h_token,percent_7d_token, rsi_value, total_end)
    return orderid, priceorder, qty, status

#execute
handler()