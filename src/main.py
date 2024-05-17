from processing import check_balance_and_trade
from messaging_bot import bot_telegram
from config import Config
import transaction_handler
    
config_file = 'config.ini'
config = Config(config_file)
statistic_token = config.get_statistic_token()
statistic_global = config.get_statistic_global()
get_index_feargreed = config.get_index_feargreed()
ADDRESS_BINGX_ETH = config.get_address_bingx()
token_symbol = config.get_token_symbol()
network_blockchain = config.get_blockchain_network()
address_tag = config.get_tag_wallet()
address_destination = config.get_token_address()
current_time = config.get_current_time()
 
def lambda_handler(event, context):
    """
    Create a handler function that can be used as handler in AWS Lambda console.

    Parameters:
    - event (dict): AWS Lambda event data.
    - context (LambdaContext): AWS Lambda context data.

    Returns:
    - dict: A dictionary containing a simple status code.        
    """
    for i in range(len(token_symbol)): #enable this loop when it becomes possible to implement the purchase of more than 1 token
        qty_token = transaction_handler.get_balance(token_symbol[i], current_time)
        price_low, price_current, price_last = transaction_handler.get_price(token_symbol[i], current_time)
        if qty_token is not None:
            check_balance_and_trade(round(qty_token * price_current,2), qty_token, token_symbol[i], network_blockchain[i], address_destination[i], address_tag[i], current_time)
        else: 
            bot_telegram('❌Alert\\!\n\nAPI error on '+current_time.replace('-', '\\-')
                +' \\(GMT\\-5\\)\\.\n\nFunction failure: qty\\_token is null')
    return {
        'statusCode': 200,
    }

#local test
#call the lambda_handler function locally
if __name__ == "__main__":
    lambda_handler({'key1': 'value1', 'key2': 'value2'}, {})