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


class TmallScraper(TaobaoScraper):
    def __init__(self, products_limit=10, sleep_time=0):
        super().__init__(products_limit, sleep_time)
        self.cookies_path = 'cookies/taobao.pkl'
        self.cookies_name = 'taobao'
        self.url = 'https://www.taobao.com/'
        self.login_url = self.url
        self.store_name = 'tmall'

    def scrape_product_info(self, product_name, headless=False):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://s.taobao.com/search?fromTmallRedirect=true&page=1&q={product_name}&tab=mall"

        driver = self.login(headless=headless)
        driver.get(search_url)
        soup = BeautifulSoup(driver.page_source, 'lxml')

        def criteria(tag):
            return tag.find(class_='Price--priceInt--ZlsSi_M') and tag.find(class_='Title--title--jCOPvpf') \
                   and tag.find(class_='Card--mainPicAndDesc--wvcDXaK') \
                   and not tag.find(class_='Card--doubleCard--wznk5U4') and not tag.find(class_='Card--doubleCardWrapper--L2XFE73')

        divs = soup.find_all(criteria)

        def criteria(tag):
            return tag.name == 'a' and tag.get('class') and 'Card--doubleCardWrapper--L2XFE73' in tag.get('class')

        a_tags = soup.find_all(criteria)
        urls = [a['href'] for a in a_tags]

        products = []
        for div, url in zip(divs, urls):
            price_int = div.select_one('.Price--priceInt--ZlsSi_M')
            price_float = div.select_one('.Price--priceFloat--h2RR0RK')
            name = div.select_one('.Title--title--jCOPvpf')
            merchant = div.select_one('.ShopInfo--shopName--rg6mGmy')
            price = int(price_int.text.strip()) + float(price_float.text.strip())
            if not url.startswith('https:'):
                url = 'https:' + url
            product = {"product_name": name.text.strip(), "price": price, "merchant": merchant.text.strip(), "url": url,
                       'platform': self.store_name}
            products.append(product)
            if len(products) == self.limit:
                break

        driver.quit()

        return products


def test_scraper():
    scraper = TaobaoScraper(products_limit=10, sleep_time=1)
    products = ['丹麦皇冠木烟熏蒸煮香肠200g'
        #'丹麦皇冠慕尼黑风味白肠500g',
                #'丹麦皇冠慕尼黑风味白肠800g', '丹麦皇冠慕尼黑风味白肠350g',
                #'丹麦皇冠图林根风味香肠350g', '丹麦皇冠图林根风味香肠500g', '丹麦皇冠图林根风味香肠800g',
                #'丹麦皇冠西班牙风味香肠500g', '丹麦皇冠西班牙风味香肠350g', '丹麦皇冠西班牙风味香肠800g',
                #'丹麦皇冠木烟熏蒸煮香肠200g', '丹麦皇冠木烟熏蒸煮香肠1kg',
                #'丹麦皇冠木烟熏蒸煮热狗肠200g', '丹麦皇冠木烟熏蒸煮热狗肠1kg', '丹麦皇冠超值热狗肠200g', '丹麦皇冠超值热狗肠1kg'
                ]
    prices = [
        #49, 64, 32,
        #31.8, 49, 49,
        52, 27.84, 60
    ]
    #x = scraper.scrape_product_info('丹麦皇冠慕尼黑风味白肠500g')
    #print(x)
    for i, p in enumerate(products):
        print(f'Scraping product: {products[i]}')
        product_info = scraper.scrape_product_info_by_weight(p, use_gpt=True, verbose=True, headless=False)
        print(f'Target price: {prices[i]}')
        print('--------------------')
        time.sleep(5)


if __name__ == "__main__":
    test_scraper()
