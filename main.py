from hashlib import sha256
import requests
import hmac
import time

#credentials
APIURL = "https://open-api.bingx.com"
APIKEY = "YOUR-API-KEY"
SECRETKEY = "YOUR-SECRET-KEY"

#get sign request secretkey to generate a signature
def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    #print("sign=" + signature)
    return signature

#single request api call
def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
    #print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

#parameter encapsulation
def praseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    return paramsStr+"&timestamp="+str(int(time.time() * 1000))