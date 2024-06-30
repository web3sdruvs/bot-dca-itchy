from datetime import datetime
import configparser
import pytz

class Config:
    """
    A class for managing configuration settings, particularly related to API keys,
    blockchain addresses, and various URLs. It also provides methods to retrieve
    specific configuration values.

    Attributes:
    - config_file (str): The path to the configuration file.

    Methods:
    - get_api_url_bingx(): Retrieve the API URL for BingX.
    - get_api_key_bingx(): Retrieve the API key for BingX.
    - get_api_secretkey_bingx(): Retrieve the secret key for BingX.
    - get_address_bingx(): Retrieve the blockchain address for BingX (ETH).
    - get_api_key_telegram(): Retrieve the API key for the Telegram bot.
    - get_api_chatkey_telegram(): Retrieve the chat key for the Telegram bot.
    - get_statistic_token(): Retrieve the alternative API URL for token statistics.
    - get_statistic_global(): Retrieve the alternative API URL for global statistics.
    - get_index_feargreed(): Retrieve the alternative API URL for fear and greed index.
    - get_token_symbol(): Retrieve a list of token symbols from the configuration.
    - get_token_address(): Retrieve a list of blockchain addresses from the configuration.
    - get_blockchain_network(): Retrieve a list of blockchain networks from the configuration.
    - get_tag_wallet(): Retrieve a list of wallet tags from the configuration.
    - get_current_time(): Retrieve the current time in the 'America/Cayman' timezone.
    - get_bucket_name(): Retrieve the AWS S3 bucket name for the bot's data.

    """
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
    
    def get_list_blockchain_network(self):
        return dict(self.config['LIST_BLOCKCHAIN_ADDRESS'])

    def get_tag_wallet(self):
        return list(self.config['TAG'].values())
    
    def get_current_time(self):
        timezone_summer = pytz.timezone('America/Cayman')
        current_time = datetime.now(timezone_summer)
        current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        return current_time

    def get_bucket_name(self):
        return self.config['AWS']['BUCKET_BOT_DCA_ITCHY']