from bs4 import BeautifulSoup
from selenium import webdriver
import pickle
import os
from scraper_base import BaseScraper


class JDScraper(BaseScraper):
    def __init__(self, products_limit=10):
        super().__init__(products_limit)
        self.cookies_path = 'cookies/jd.pkl'
        self.cookies_name = 'jd'
        self.url = 'https://www.jd.com'
        self.login_url = 'https://passport.jd.com/new/login.aspx'
        self.store_name = 'jd'

    def scrape_product_info(self, product_name):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://search.jd.com/Search?keyword={product_name}"

        driver = webdriver.Chrome()
        driver.get(self.url)
        cookies = pickle.load(open(self.cookies_path, 'rb'))  # login domain different from search domain
        #print([cookie for cookie in cookies])
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()

        driver.get(search_url)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        #print(soup)

        prices = soup.find_all('div', {'class': 'p-price'})
        names = soup.find_all('div', {'class': 'p-name p-name-type-2'})

        products = []
        for name, price in zip(names, prices):
            price = price.text.strip().split('\n')[0]
            price = float(price.replace('￥', ''))
            product = {"name": name.text.strip(), "price": price}
            products.append(product)
            if self.limit is not None and len(products) == self.limit:
                break

        driver.quit()

        return products

