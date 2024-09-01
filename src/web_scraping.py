from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from time import sleep
import warnings
import requests

warnings.simplefilter('ignore', InsecureRequestWarning)

class IndexFearGreed:
  def __init__(self, find='a', url='https://coinmarketcap.com'):
    '''
    Constructs all the necessary attributes for the IndexFearGreed object.

    Parameters:
        find (str): The HTML element to find in the webpage (default is 'a').
        url (str): The URL of the webpage to scrape (default is 'https://coinmarketcap.com').
    '''
    self.find = find.lower()
    self.url = url.lower()

  def __get_web_scraping(self):
    '''
    Perform web scraping on the given URL and return a list of found elements.

    This method sends a GET request to the specified URL with appropriate headers,
    parses the HTML content using BeautifulSoup, and finds all elements matching
    the specified tag.

    Returns:
        list: A list of found HTML elements.
    '''
    _headers = {
          'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'pt-BR,pt;q=0.5',
          'Accept-Encoding': 'gzip, deflate',
          'Upgrade-Insecure-Requests': '1'
    }

    with requests.Session() as session:
      _response = session.get(f'{self.url}', headers = _headers, verify = True)
      _response.raise_for_status()
      _bs4_html = BeautifulSoup(_response.content, "html.parser")
      _element = _bs4_html.find_all(self.find)
    return _element

  def get_index_fear_greed_coinmarketcap(self):
    '''
    Extract the Fear & Greed index from the scraped elements and return it as an integer.

    This method calls the __get_web_scraping method to retrieve the HTML elements,
    extracts the Fear & Greed index from the specified element, and returns it as an integer.

    Returns:
        int: The Fear & Greed index if successful, or -1 if an error occurs or not enough elements are found.
    '''
    try:
      _element = self.__get_web_scraping()
      if len(_element) > 10:
        _index = int(_element[10].text.split('/')[0])
        return _index
      else:
        return -1
    except Exception as e:
      return -1