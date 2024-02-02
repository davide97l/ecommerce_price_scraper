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
        merchants = soup.find_all('div', {'class': 'p-shop'})
        divs_href = soup.find_all('div', class_='p-img')
        urls = [div.find('a')['href'] for div in divs_href if div.find('a') and div.find('a').has_attr('href')]

        products = []
        for name, price, merchant, url in zip(names, prices, merchants, urls):
            price = price.text.strip().split('\n')[0]
            price = float(price.replace('￥', ''))
            name = name.text.strip().replace('\n', ' ')
            if not url.startswith('https:'):
                url = 'https:' + url
            product = {"product_name": name, "price": price, "merchant": merchant.text.strip(), "url": url}
            products.append(product)
            if self.limit is not None and len(products) == self.limit:
                break

        driver.quit()

        return products


def test_scraper():
    scraper = JDScraper(products_limit=10)
    products = scraper.get_product_info('kinder bueno')
    print(products)


if __name__ == "__main__":
    test_scraper()