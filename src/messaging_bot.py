from logging import info, error, basicConfig, INFO
from config import Config
import telepot

basicConfig(level=INFO, format='%(asctime)s - %(levelname)s - %(message)s')   
config_file = 'config.ini'
config = Config(config_file)
BOTKEY = config.get_api_key_telegram()
CHATKEY = config.get_api_chatkey_telegram()
BOTKEY = telepot.Bot(BOTKEY)

def bot_telegram(msg_text):
    """
    Send a message to a specified Telegram chat using the provided message text.

    Parameters:
    - msg_text (str): The text of the message to be sent.

    Returns:
    - None
    """
    try:
        info(f'Function bot_telegram')
        BOTKEY.sendMessage(CHATKEY, msg_text, parse_mode='MarkdownV2')
    except:
        error(f'Function bot_telegram')