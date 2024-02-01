from bs4 import BeautifulSoup
from selenium import webdriver
import pickle
import os
from scraper_base import BaseScraper


class TaobaoScraper(BaseScraper):
    def __init__(self, products_limit=10):
        super().__init__(products_limit)
        self.cookies_path = 'cookies/taobao.pkl'
        self.cookies_name = 'taobao'
        self.url = 'https://www.taobao.com/'
        self.login_url = self.url
        self.store_name = 'taobao'

    def scrape_product_info(self, product_name):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://s.taobao.com/search?page=1&q={product_name}&tab=all"

        driver = webdriver.Chrome()
        driver.get(self.url)
        cookies = pickle.load(open(self.cookies_path, 'rb'))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()

        driver.get(search_url)
        soup = BeautifulSoup(driver.page_source, 'lxml')

        def criteria(tag):
            # filter tmall items
            return not tag.find(class_='Title--iconPic--kYJcAc0') \
                   and tag.find(class_='Price--priceInt--ZlsSi_M') and tag.find(class_='Title--title--jCOPvpf') \
                   and tag.find(class_='Card--mainPicAndDesc--wvcDXaK') \
                   and not tag.find(class_='Card--doubleCard--wznk5U4') and not tag.find(class_='Card--doubleCardWrapper--L2XFE73')

        divs = soup.find_all(criteria)

        products = []
        for div in divs:
            price_int = div.select_one('.Price--priceInt--ZlsSi_M')
            price_float = div.select_one('.Price--priceFloat--h2RR0RK')
            name = div.select_one('.Title--title--jCOPvpf')
            price = int(price_int.text.strip()) + float(price_float.text.strip())
            product = {"name": name.text.strip(), "price": price}
            products.append(product)
            if len(products) == self.limit:
                break

        driver.quit()

        return products

