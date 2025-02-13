from logging import info, error, basicConfig, INFO
from processing import check_balance_and_trade
from messaging_bot import bot_telegram
from transaction_handler import get_balance, get_price
from config import Config

basicConfig(level=INFO, format='%(asctime)s - %(levelname)s - %(message)s')   
config_file = 'config.ini'
config = Config(config_file)
token_symbol = config.get_token_symbol()
network_blockchain_list = config.get_blockchain_network_dict()
address_tag_list = config.get_tag_wallet_dict()
address_destination_list = config.get_token_address_dict()
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
        info(f'Function lambda_handler: token {token_symbol[i]}')
        qty_token = get_balance(token_symbol[i], current_time)
        price_low, price_current, price_last = get_price(token_symbol[i], current_time)
        network_blockchain = network_blockchain_list[token_symbol[i].lower()]
        address_destination = address_destination_list[network_blockchain.lower()]
        address_tag = address_tag_list[token_symbol[i].lower()]
        if qty_token is not None:
            check_balance_and_trade(round(qty_token * price_current,2), qty_token, token_symbol[i], network_blockchain, address_destination, address_tag, current_time)
        else: 
            error(f'Function lambda_handler: token {token_symbol}')
            bot_telegram('❌Alert\\!\n\nAPI error on '+current_time.replace('-', '\\-')
                +' \\(GMT\\-5\\)\\.\n\nFunction failure: qty\\_token is null')
    info('Execution completed')
    return {
        'statusCode': 200,
    }

#local test
#call the lambda_handler function locally
if __name__ == "__main__":
    lambda_handler({'key1': 'value1', 'key2': 'value2'}, {})