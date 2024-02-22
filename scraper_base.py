from selenium import webdriver
import time
import re
from selenium.webdriver.chrome.options import Options
from operator import itemgetter
from openai import OpenAI
from fake_useragent import UserAgent
import random
import requests
from requests_ip_rotator import ApiGateway, DEFAULT_REGIONS
import os
import pickle
from dotenv import load_dotenv
load_dotenv()


class BaseScraper:
    def __init__(self, products_limit=10, sleep_time=0):
        self.limit = products_limit
        self.store_name = None
        self.cookies_path = None
        self.cookies_name = None
        self.url = None
        self.login_url = None
        self.sleep_time = sleep_time
        self.sleep_var = 2.

    def scrape_product_info(self, product_name):
        pass

    def scrape_product_info_by_weight(self, product_name):
        pass

    def sleep(self):
        time.sleep(random.uniform(max(self.sleep_time-self.sleep_var, 0), max(self.sleep_time+self.sleep_var, 0))
                   if self.sleep_time > 0 else 0)

    @staticmethod
    def get_weight_from_product_name(product_name):
        try:
            weight = re.findall(r'(\d+(?:g|kg))', product_name)  # extract kg and g
            if weight:
                updated_product_name = product_name.replace(weight[0], '').strip()
            else:
                updated_product_name = product_name
        except:
            return None, product_name
        return weight[0] if weight else None, updated_product_name

    @staticmethod
    def check_name_matching_gpt(item1, item2):
        #print(item1, item2)
        load_dotenv()
        client = OpenAI(
            # This is the default and can be omitted
            api_key=os.getenv('OPENAI_KEY'),
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": 'assistant',
                    "content": """
                    Act as a ecommerce products comparator.
                    Given as input two items tell if they refer to the same item or they are different ones. 
                    Ignore the brand and focus on the weight and type of item. For example 丹麦皇冠西班牙风味香肠500g and 西班牙风味香肠500g are the same.
                    If the type of the item is not specified, they are not the same item. For example 西班牙风味香肠 and 香肠 are different.
                    Different weights also refer to different items. For example 西班牙风味香肠500g and 西班牙风味香肠800g are different.
                    The type can be the same even if written in different ways. For example 丹麦皇冠西班牙风味香肠500g and 丹麦皇冠西班牙香肠500g are the same.
                    Just return True or False based on your conclusion.
                    \nItem 1: {}\nItem 2: {}""".format(item1, item2)
                }
            ],
            model="gpt-4",
        )
        response = str(chat_completion.choices[0].message.content.strip()).lower()
        return True if 'true' in response else False

    @staticmethod
    def check_name_matching_score(reference_product, product_name, remove_punctuation=False):
        if remove_punctuation:
            product_name = ''.join(char if char.isalnum() or char.isspace() else '' for char in product_name)
            reference_product = ''.join(char if char.isalnum() or char.isspace() else '' for char in reference_product)
        matching_chars = set(char for char in product_name if char in reference_product)
        non_matching_chars = set(char for char in product_name if char not in reference_product)
        return len(matching_chars) - len(non_matching_chars)

    def get_best_matching_product(self, product_name, products_info):
        product_scores = []
        for i, product in enumerate(products_info):
            match_score = self.check_name_matching_score(product['product_name'], product_name)
            product_scores.append({'product': product, 'score': match_score})
        sorted_product_scores = sorted(product_scores, key=itemgetter('score'), reverse=True)
        sorted_scores = [product_score['score'] for product_score in sorted_product_scores]
        sorted_products = [product_score['product'] for product_score in sorted_product_scores]
        return sorted_products, sorted_scores

    def login(self, headless=False, playwright=None, selenium=False):
        ip_address = requests.get('https://api.ipify.org').text
        print(f"Public IP Address: {ip_address}")

        # Set up fake user agent
        ua = UserAgent()
        userAgent = ua.random
        print(userAgent)

        if not os.path.isfile(self.cookies_path):
            print('Cookie not detected, please login to save cookies')
            self.get_cookies(self.login_url, cookies_name=self.cookies_name)

        if selenium:
            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f'user-agent={userAgent}')
            driver = webdriver.Chrome(options=options)
            driver.get(self.url)
            cookies = pickle.load(open(self.cookies_path, 'rb'))
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.refresh()
            return driver

        if playwright is not None:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent=userAgent
            )
            with open(self.cookies_path, 'rb') as f:
                cookies = pickle.load(f)
            context.add_cookies(cookies)

            return browser, context

    @staticmethod
    def get_cookies(url, cookies_name='cookies', save_dir='cookies'):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        driver = webdriver.Chrome()
        driver.get(url)  # Navigate to your URL

        print(f'Now you can login')
        print('Press any button to continue after you have logged in...')
        input()

        # This creates cookies.pkl and saves the cookies:
        cookies_path = os.path.join(save_dir, f"{cookies_name}.pkl")
        pickle.dump(driver.get_cookies(), open(cookies_path, "wb"))
        print(f'Cookies saved at {cookies_path}')

        driver.quit()

    @staticmethod
    def remove_duplicates(list_of_dict, key):
        new_list_of_dict = []
        for d in list_of_dict:
            if d[key] not in [nd[key] for nd in new_list_of_dict]:
                new_list_of_dict.append(d)
        return new_list_of_dict

    @staticmethod
    def get_proxy_url(url):
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
        return proxy_url, gateway
