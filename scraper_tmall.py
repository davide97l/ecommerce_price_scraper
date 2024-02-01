from bs4 import BeautifulSoup
from selenium import webdriver
import pickle
import os
from scraper_base import BaseScraper


class TmallScraper(BaseScraper):
    def __init__(self, products_limit=10):
        super().__init__(products_limit)
        self.cookies_path = 'cookies/taobao.pkl'
        self.cookies_name = 'taobao'
        self.url = 'https://www.taobao.com/'
        self.login_url = self.url
        self.store_name = 'tmall'

    def scrape_product_info(self, product_name):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://s.taobao.com/search?fromTmallRedirect=true&q={product_name}&tab=mall"

        driver = webdriver.Chrome()
        driver.get(self.url)
        cookies = pickle.load(open(self.cookies_path, 'rb'))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()

        driver.get(search_url)
        soup = BeautifulSoup(driver.page_source, 'lxml')

        prices_int = soup.select('.Price--priceInt--ZlsSi_M')
        prices_float = soup.select('.Price--priceFloat--h2RR0RK')
        names = soup.select('.Title--title--jCOPvpf')

        products = []
        for name, price_int, price_float in zip(names, prices_int, prices_float):
            price = int(price_int.text.strip()) + float(price_float.text.strip())
            product = {"name": name.text.strip(), "price": price}
            products.append(product)
            if len(products) == self.limit:
                break

        driver.quit()

        return products
