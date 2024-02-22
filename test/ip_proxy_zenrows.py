import pickle
from zenrows import ZenRowsClient
import urllib.parse

#https://www.zenrows.com/

client = ZenRowsClient('your_zenrows_api_key')

search_item = '丹麦皇冠木烟熏蒸煮香肠200g'
x = urllib.parse.quote(search_item)  # URL encode the query
url = f'https://s.taobao.com/search#?fromTmallRedirect=true&page=1&q={x}&tab=mall'

# Load cookies from .pkl file
with open('../cookies/taobao.pkl', 'rb') as file:
    cookies_list = pickle.load(file)

cookies = {cookie['name']: cookie['value'] for cookie in cookies_list}

response = client.get(url, cookies=cookies)

print(response.text)

