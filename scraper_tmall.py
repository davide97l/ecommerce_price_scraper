import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
import pickle
import os
from scraper_base import BaseScraper
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from scraper_taobao import TaobaoScraper
from playwright.sync_api import sync_playwright
import asyncio


class TmallScraper(TaobaoScraper):
    def __init__(self, products_limit=10, sleep_time=0):
        super().__init__(products_limit, sleep_time)
        self.cookies_path = 'cookies/taobao.pkl'
        self.cookies_name = 'taobao'
        self.url = 'https://www.taobao.com/'
        self.login_url = self.url
        self.store_name = 'tmall'

    def scrape_product_info(self, product_name, headless=False, verbose=False):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://s.taobao.com/search?fromTmallRedirect=true&page=1&q={product_name}&tab=mall"
        if verbose: print(search_url)

        with sync_playwright() as playwright:
            browser, context = self.login(playwright=playwright)

            # Open new page
            page = context.new_page()
            page.goto(search_url)
            source_code = page.content()
            #print(source_code)

            products = []
            items = page.query_selector_all('.Card--doubleCardWrapperMall--uPmo5Bz')
            for item in items:
                name = item.query_selector('.Title--title--jCOPvpf').text_content()
                price_int = item.query_selector('.Price--priceInt--ZlsSi_M').text_content()
                price_float = item.query_selector('.Price--priceFloat--h2RR0RK').text_content()
                merchant = item.query_selector('.ShopInfo--shopName--rg6mGmy').text_content()
                price = int(price_int.strip()) + float(price_float.strip())
                url = item.get_attribute('href')
                if not url.startswith('https:'):
                    url = 'https:' + url
                product = {"product_name": name.strip(), "price": price, "merchant": merchant.strip(), "url": url,
                           'platform': self.store_name}
                products.append(product)
                if len(products) == self.limit:
                    break

            page.close()
            browser.close()

        return products


def test_scraper():
    scraper = TmallScraper(products_limit=10, sleep_time=3)
    products = [
        '丹麦皇冠木烟熏蒸煮香肠200g'
    ]
    prices = [
        21.9
    ]
    for i, p in enumerate(products):
        print(f'Scraping product: {products[i]}')
        product_info = scraper.scrape_product_info_by_weight(p, use_gpt=True, verbose=True, headless=True)
        print(f'Target price: {prices[i]}')
        print('--------------------')
        time.sleep(5)


if __name__ == "__main__":
    test_scraper()
