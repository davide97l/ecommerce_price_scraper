from selenium import webdriver
import pickle
import time
import os
import pandas as pd


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
