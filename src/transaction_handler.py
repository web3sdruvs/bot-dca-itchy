from logging import info, error, basicConfig, INFO
from datetime import datetime, timedelta
from messaging_bot import bot_telegram
from config import Config
import credential
import boto3
import time
import json
import re

basicConfig(level=INFO, format='%(asctime)s - %(levelname)s - %(message)s')           
config_file = 'config.ini'
config = Config(config_file)
BUCKET_BOT_DCA_ITCHY = config.get_bucket_name()
re_default = r'[^a-zA-Z0-9\s]'

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
    info(f'Function get_balance: token {symbol}')
    _payload = {}
    _path = '/openApi/spot/v1/account/balance'
    _method = 'GET'
    _params_map = {
    'recvWindow': 0
    }
    _params_str = credential.prase_param(_params_map)
    _json_data = json.loads(credential.send_request(_method, _path, _params_str, _payload))

    if 'data' in _json_data:  
        _amount = 0.0  
        for _balance in _json_data['data']['balances']:
            if _balance['asset'] == symbol:
                _amount = round(float(_balance['free']),8)
        return _amount
    else:
        error(f'Function get_balance: token {symbol}') 
        _error = _json_data['msg']
        _error = re.sub(re_default, ' ', str(_error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: get\\_balance\n\nError: '+_error)
        return _error

def request_withdraw(symbol, network, address, addressTag, _amount, timestamp):
    """
    Initiate a withdrawal request for a specific cryptocurrency.

    Parameters:
    - symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH').
    - network (str): The network for the withdrawal (e.g., 'BTC', 'ERC20').
    - address (str): The destination address for the withdrawal.
    - addressTag (str): Address tag or memo for certain cryptocurrencies.
    - _amount (float): The _amount of cryptocurrency to withdraw.
    - timestamp (str): Timestamp used for error logging.

    Returns:
    - int: If successful, returns the withdrawal request ID.
    - str: If an error occurs, returns the error message.
    """
    info(f'Function request_withdraw: token {symbol}')
    _payload = {}
    _path = '/openApi/wallets/v1/capital/withdraw/apply'
    _method = 'POST'
    _params_map = {
    'coin': symbol,
    'network': network,
    'address': address,
    'addressTag': addressTag,
    '_amount': _amount,
    'walletType': 1
    }
    _params_str = credential.prase_param(_params_map)
    _json_data = json.loads(credential.send_request(_method, _path, _params_str, _payload))

    if 'data' in _json_data:  
        result = _json_data['data']['id']
        bot_telegram('✅Withdrawal Successful\n\nYou have sucessfully withdrawn '+str(_amount).replace('.', '\\.')
            +' '+symbol+' on '+timestamp.replace('-', '\\-')+' \\(GMT\\-5\\)\\.\n\nDestination address:\n\n`'
            +address+'`\n\nTransaction ID:\n`'+str(result)+'`')
        return result
    else:
        error(f'Function request_withdraw: token {symbol}')
        _error = _json_data['msg']
        _error = re.sub(re_default, ' ', str(_error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: request\\_withdraw\n\nError: '+_error)
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
    info(f'Function get_withdrawfee: token {symbol}')
    network_fee = float(0.0)
    network = network.upper()
    _payload = {}
    _path = '/openApi/wallets/v1/capital/config/getall'
    _method = "GET"
    _params_map = {
    "recvWindow": 0
    }
    _params_str = credential.prase_param(_params_map)
    _json_data = json.loads(credential.send_request(_method, _path, _params_str, _payload))
    
    if 'data' in _json_data:  
      _json_data = _json_data['data']
      for i in _json_data:
        network_list = i.get("networkList", [])
        for fee  in network_list:
          if fee.get("name") == symbol and fee.get("network") == network:
            network_fee = float(fee['withdrawFee'])
            return network_fee
    else: 
        error(f'Function get_withdrawfee: token {symbol}')
        _error = _json_data['msg']
        _error = re.sub(re_default, ' ', str(_error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                +' \\(GMT\\-5\\)\\.\n\nFunction failure: get\\_withdrawfee\n\nError: '+_error)
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
    info(f'Function place_order: token {symbol}')
    _payload = {}
    _path = '/openApi/spot/v1/trade/order'
    _method = 'POST'
    _params_map = {
    'symbol': symbol+'-USDT',
    'side': 'BUY', #BUY/SELL
    'type': 'MARKET', #MARKET/LIMIT
    'timeInForce': 'POC', #IOC = immediate-or-cancel , POC = process-or-cancel
    'quoteOrderQty': quantity,
    'recvWindow': 0
    }
    _params_str = credential.prase_param(_params_map)
    _json_data = json.loads(credential.send_request(_method, _path, _params_str, _payload))
    if 'data' in _json_data:
        orderId = _json_data['data']['orderId']
        priceOrder = round(float(_json_data['data']['price']),3)
        qty = float(_json_data['data']['executedQty'])
        status = str(_json_data['data']['status']).lower()
        total = round(qty*priceOrder,3)
        flag = '✅' if status != 'canceled' else '❌'
        bot_telegram(flag+'Buy order '+status+'\n\nOrder ID: `'
                     +str(orderId)+'`\nDate: '+timestamp.replace('-', '\\-')+' \\(GMT\\-5\\)\\\nToken: '
                     +symbol+'\nPrice: \\$'+str(priceOrder).replace('.', '\\.')+'\n_amount: '
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
        error(f'Function place_order: token {symbol}')
        _error = _json_data['msg']
        _error = re.sub(re_default, ' ', str(_error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: place\\_order\n\nError: '+_error)
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
    info(f'Function cancel_order: token {symbol}')
    _payload = {}
    _path = '/openApi/spot/v1/trade/cancel'
    _method = 'POST'
    _params_map = {
    'symbol': symbol +'-USDT',
    'orderId': orderId,
    'recvWindow': 0
    }
    _params_str = credential.prase_param(_params_map)
    _json_data = json.loads(credential.send_request(_method, _path, _params_str, _payload))
    
    if 'data' in _json_data:
        client_order_id = _json_data['data']['client_order_id']
        return client_order_id
    else: 
        error(f'Function cancel_order: token {symbol}')
        _error = _json_data['msg']
        _error = re.sub(re_default, ' ', str(_error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: cancel\\_order\n\nError: '+_error)
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
    info(f'Function get_price: token {symbol}')
    _payload = {}
    _path = '/openApi/spot/v1/ticker/24hr'
    _method = 'GET'
    _params_map = {
    'symbol': symbol +'-USDT'
    }
    _params_str = credential.prase_param(_params_map)
    _json_data = json.loads(credential.send_request(_method, _path, _params_str, _payload))

    if 'data' in _json_data: 
        low = round(_json_data['data'][0]['lowPrice'],4)
        current = round(_json_data['data'][0]['lastPrice'],4)
        changes = round(_json_data['data'][0]['openPrice'],4)
        return low, current, changes
    else:
        error(f'Function get_price: token {symbol}')
        _error = _json_data['msg']
        _error = re.sub(re_default, ' ', str(_error))
        bot_telegram('❌Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: price\\_current\n\nError: '+_error)
        return error

def get_candlestick_chart_data(symbol, timestamp, limit=14, interval='1d'):
    """
    Fetch candlestick chart data for a specified cryptocurrency symbol.

    This function retrieves candlestick  data for a given cryptocurrency
    symbol against USDT from an API. The data fetched covers the past 14 days by default
    with a specified interval.

    Args:
        symbol (str): The cryptocurrency symbol to fetch data for (e.g., 'BTC').
        timestamp (str): The current timestamp in a specific format.
        limit (int, optional): The maximum number of data points to retrieve. Defaults to 14.
        interval (str, optional): The interval for each candlestick (e.g., '1d', '1h'). Defaults to '1d'.

    Returns:
        dict: The JSON response containing candlestick data if successful.
        str: The error message if the API call fails.
    """
    info(f'Function get_candlestick_chart_data: token {symbol}')
    current_datetime = datetime.now()
    resultant_date = current_datetime - timedelta(days=14)
    desired_time = datetime(resultant_date.year, resultant_date.month, resultant_date.day, 15, 59, 59)
    start_epoch_timestamp = int(str(int(desired_time.timestamp()))+'000')
    end_epoch_timestamp = int(str(int(time.time()))+'000')
    _payload = {}
    _path = '/openApi/spot/v1/market/kline'
    _method = 'GET'
    _params_map = {
    'symbol': symbol +'-USDT',
    'interval': interval,
    'startTime': start_epoch_timestamp,
    'endTime': end_epoch_timestamp,
    'limit' : limit
    }  
    _params_str = credential.prase_param(_params_map)
    _json_data = json.loads(credential.send_request(_method, _path, _params_str, _payload))
    
    if 'data' in _json_data:
      return _json_data  
    else:
        error(f'Function get_candlestick_chart_data: token {symbol}')
        _error = _json_data['msg']
        _error = re.sub(re_default, ' ', str(_error))
        bot_telegram('✅Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: get\\_candlestick\n\nError: '+_error)
        return error