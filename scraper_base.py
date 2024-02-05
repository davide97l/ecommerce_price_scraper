from selenium import webdriver
import pickle
import time
import os
import pandas as pd
import re
import numpy as np
from selenium.webdriver.chrome.options import Options


class BaseScraper:
    def __init__(self, products_limit=10):
        self.limit = products_limit
        self.store_name = None
        self.cookies_path = None
        self.cookies_name = None
        self.url = None
        self.login_url = None
        pass

    def scrape_product_info(self, product_name):
        pass

    def get_product_info(self, product_name):
        if not os.path.isfile(self.cookies_path):
            print('Cookie not detected, please login so save cookies')
            self.get_cookies(self.login_url, cookies_name=self.cookies_name)
        products_info = self.scrape_product_info(product_name)
        return products_info

    def get_product_df(self, product_name):
        df = pd.DataFrame(self.get_product_info(product_name))
        df['platform'] = self.store_name
        return df

    @staticmethod
    def get_weight_from_product_name(product_name):
        try:
            weight = re.findall(r'(\d+g)', product_name)
            if weight:
                updated_product_name = product_name.replace(weight[0], '').strip()
            else:
                updated_product_name = product_name
        except:
            return None, product_name
        return weight[0] if weight else None, updated_product_name

    @staticmethod
    def check_name_matching(reference_product, product_name, remove_punctuation=False):
        if remove_punctuation:
            product_name = ''.join(char if char.isalnum() or char.isspace() else '' for char in product_name)
            reference_product = ''.join(char if char.isalnum() or char.isspace() else '' for char in reference_product)
        # return True if all characters in product_name are present in reference_product
        if all(char in reference_product for char in product_name):
            return True
        return False

    @staticmethod
    def check_name_matching_score(reference_product, product_name, remove_punctuation=False):
        if remove_punctuation:
            product_name = ''.join(char if char.isalnum() or char.isspace() else '' for char in product_name)
            reference_product = ''.join(char if char.isalnum() or char.isspace() else '' for char in reference_product)
        matching_chars = set(char for char in product_name if char in reference_product)
        non_matching_chars = set(char for char in product_name if char not in reference_product)
        return len(matching_chars) - len(non_matching_chars)

    def get_best_matching_product(self, product_name, products_info):
        # TODO if input is df convert it to dict
        best_match_product_idx = 0
        best_match_product_score = -np.Inf
        for i, product in enumerate(products_info):
            match_score = self.check_name_matching_score(product['product_name'], product_name)
            if match_score > best_match_product_score:
                best_match_product_idx = i
                best_match_product_score = match_score
            print(product['product_name'], product_name, match_score, best_match_product_score, best_match_product_idx)
        return best_match_product_idx

    def login(self):
        options = Options()
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537')
        driver = webdriver.Chrome(options=options)
        #driver = webdriver.Chrome()
        driver.get(self.url)
        cookies = pickle.load(open(self.cookies_path, 'rb'))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        return driver

    @staticmethod
    def get_cookies(url, login_time=30, cookies_name='cookies', save_dir='cookies'):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        driver = webdriver.Chrome()
        driver.get(url)  # Navigate to your URL

        print(f'Now you have {login_time}s to login')
        time.sleep(login_time)

        # This creates cookies.pkl and saves the cookies:
        cookies_path = os.path.join(save_dir, f"{cookies_name}.pkl")
        pickle.dump(driver.get_cookies(), open(cookies_path, "wb"))
        print(f'Cookies saved at {cookies_path}')

        driver.quit()
