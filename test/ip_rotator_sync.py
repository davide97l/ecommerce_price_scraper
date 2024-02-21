from requests_ip_rotator import ApiGateway, DEFAULT_REGIONS
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
load_dotenv()

url = 'https://api.ipify.org'

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
        headless=True,
    )
    for i in range(5):
        page = browser.new_page()
        page.goto(proxy_url)
        print(page.content())
    browser.close()

# Shut down the API Gateway
gateway.shutdown()
