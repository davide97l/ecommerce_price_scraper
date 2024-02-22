from requests_ip_rotator import ApiGateway, DEFAULT_REGIONS
import os
import pickle
import urllib.parse
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from playwright_stealth import stealth_sync
load_dotenv()

search_item = '丹麦皇冠木烟熏蒸煮香肠200g'
x = urllib.parse.quote(search_item)  # URL encode the query
url = f'https://s.taobao.com/search#?fromTmallRedirect=true&page=1&q={x}&tab=mall'

# Set up and start API Gateway
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_access_key_secret = os.getenv('AWS_SECRET_ACCESS_KEY')

# Ensure that the regions you want to use are available and enabled in your AWS account.
gateway = ApiGateway(url, regions=DEFAULT_REGIONS,
                     access_key_id=aws_access_key_id, access_key_secret=aws_access_key_secret)
endpoints = gateway.start()

# Ensure endpoints are generated.
if not endpoints:
    raise Exception("No endpoints were created. Check your AWS configuration.")

proxy_endpoint = endpoints[0]
proxy_url = f'https://{proxy_endpoint}/ProxyStage/'
print("Proxy endpoint for Playwright:", proxy_url)

# Use Playwright with the API Gateway as a proxy
with sync_playwright() as p:
    # Specify the correct protocol, probably HTTP
    browser = p.chromium.launch(
        headless=False,
    )
    context = browser.new_context()
    with open('../cookies/taobao.pkl', 'rb') as f:
        cookies = pickle.load(f)
    context.add_cookies(cookies)

    page = context.new_page()
    stealth_sync(page)
    page.goto(proxy_url)
    items = page.query_selector_all('.Card--doubleCardWrapperMall--uPmo5Bz')
    print(f'Found {len(items)} items')
    for item in items:
        title_element = item.query_selector('.Title--title--jCOPvpf')
        if title_element:  # Check if the element was found
            title = title_element.text_content()
            print(f'Title: {title}')
    input('Check if working then press to continue...')

    context.close()
    browser.close()

# Shut down the API Gateway
gateway.shutdown()
