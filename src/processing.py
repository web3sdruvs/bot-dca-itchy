from transaction_handler import get_candlestick_chart_data, place_order, get_balance, get_withdrawfee
from fetch_data import get_index_fear_greed, get_statistic_global, get_statistic_token
from logging import info, error, basicConfig, INFO
from messaging_bot import bot_telegram
from config import Config
import numpy as np
import time
import re

basicConfig(level=INFO, format='%(asctime)s - %(levelname)s - %(message)s')       
config_file = 'config.ini'
config = Config(config_file)
statistic_token = config.get_statistic_token()
statistic_global = config.get_statistic_global()
get_index_feargreed = config.get_index_feargreed()
ADDRESS_BINGX_ETH = config.get_address_bingx()
current_time = config.get_current_time()
re_default = r'[^a-zA-Z0-9\s]'

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
    info(f'Function get_rsi: token {symbol}')
    json_data = get_candlestick_chart_data(symbol, timestamp)
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
        error(f'Function get_rsi: token {symbol}')
        error = json_data['msg']
        error = re.sub(re_default, ' ', str(error))
        bot_telegram('✅Alert\\!\n\nAPI error on '+timestamp.replace('-', '\\-')
                     +' \\(GMT\\-5\\)\\.\n\nFunction failure: get\\_rsi\n\nError: '+error)
        return error
               
def check_balance_and_trade(balance, amount, symbol, network, address, tag, timestamp):  
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
    info(f'Function check_balance_and_trade: token {symbol}')
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
    info(f'Function indicators: token {symbol}')
    index_current, index_yesterday, index_last_week, index_last_month = get_index_fear_greed(get_index_feargreed)
    total_global, volume_global, dominance_btc_global = get_statistic_global(statistic_global)
    volume_24h_token, total_marketcap_token, percent_1h_token, percent_24h_token, percent_7d_token = get_statistic_token(symbol if 'WBTC' != symbol else 'BTC', statistic_token, current_time)
    rsi_value = get_rsi(symbol if 'WBTC' != symbol else 'BTC', current_time)
    array_index = [index_current, index_yesterday, index_last_week, index_last_month]
    trends = [((index_current - array_number) / array_number) * 100 for array_number in array_index]
    overview_trends = sum(trends)/len(trends)
    #index fear and greed
    match index_current:
        case index_current if index_current <= 25:
            index_w = 1
            index_class = 'Extreme Fear'
        case index_current if index_current <= 46:
            index_w = 0.7
            index_class = 'Fear'
        case index_current if  47 <= index_current <= 54:
            index_w = 0.2
            index_class = 'Neutral'
        case index_current if  55 <= index_current <= 75:
            index_w = -0.4
            index_class = 'Greed'
        case index_current if 76 <= index_current <= 100:
            index_w = -0.6
            index_class = 'Extreme Greed'
        case _:
            index_w = 0
            index_class = 'Class Invalid'

    match overview_trends:
        case overview_trends if overview_trends < -5:
            index_v = 1
        case overview_trends if overview_trends < -4:
            index_v = 0.7
        case overview_trends if overview_trends < -3:
            index_v = 0.2
        case overview_trends if overview_trends < 1:
            index_v = 0.01
        case _:
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

    match rsi_value:
        case rsi_value if rsi_value >= 70:
            rsi_w = -0.7
        case rsi_value if rsi_value >= 50:
            rsi_w = 0.6
        case rsi_value  if 30 < rsi_value < 50: 
            rsi_w = 0.8
        case rsi_value if rsi_value <= 30:
            rsi_w = 1
        case _:
            rsi_w = 0

    rsi_end = rsi_w * 1.05
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
    info(f'Function buy_dca: token {symbol}')
    index_current, index_class, dominance_btc_global, percent_1h_token, percent_24h_token,percent_7d_token, rsi_value, total_end = indicators(symbol)
    quantity = quantity if usdt <= 40 else (usdt / 8) * ((5 ** (1 / 2) + 1) / 2)
    quantity = quantity * total_end
    quantity = 5 if quantity < 5 else quantity
    quantity = usdt if (quantity > usdt) or (usdt / 2) < 6 else quantity    
    if total_end > 0.51:
        orderid, priceorder, qty, status = place_order(symbol, quantity, timestamp, index_current, index_class, dominance_btc_global, percent_1h_token, percent_24h_token,percent_7d_token, rsi_value, total_end)
        return orderid, priceorder, qty, status
    else:
        bot_telegram('⚠️Alert\\!\n\nPurchase not executed, price too inflated\\.\n\n'
                +'Token: '+symbol+'\nIndex: '+str(index_current).replace('.', '\\.')+' \\('+index_class+'\\)'
                +'\nIntensity: '+str(round(total_end,2)).replace('.', '\\.').replace('-', '\\-')
                +'\nRSI: '+str(round(rsi_value,2)).replace('.', '\\.')+'%'
                +'\nBTC Dominance: '+str(round(dominance_btc_global,2)).replace('.', '\\.')+'%'
                +'\n1H Units: '+str(round(percent_1h_token,2)).replace('.', '\\.').replace('-', '\\-')+'%\n24H Units: '
                +str(round(percent_24h_token,2)).replace('.', '\\.').replace('-', '\\-')+'%\n7D Units: '
                +str(round(percent_7d_token,2)).replace('.', '\\.').replace('-', '\\-')+'%') 