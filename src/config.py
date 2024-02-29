from datetime import datetime
import configparser
import pytz

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