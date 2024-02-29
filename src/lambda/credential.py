from hashlib import sha256
from config import Config
import numpy as np
import requests
import hmac
import time

config_file = 'config.ini'
config = Config(config_file)
APIURL_BINGX = config.get_api_url_bingx()
APIKEY_BINGX = config.get_api_key_bingx()
SECRETKEY_BINGX = config.get_api_secretkey_bingx()

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

def prase_param(params_map):
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