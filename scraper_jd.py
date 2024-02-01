import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from utils import get_cookies
import os
import pickle


def get_product_info_jd(product_name, cookies='cookies/jd.pkl', limit=10):
    product_name = product_name.lower().replace(' ', '%20')
    search_url = f"https://search.jd.com/Search?keyword={product_name}"

    driver = webdriver.Chrome()
    driver.get('https://www.jd.com')
    cookies = pickle.load(open(cookies, 'rb'))  # login domain different from search domain
    #print([cookie for cookie in cookies])
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

    driver.get(search_url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    #print(soup)

    prices = soup.find_all('div', {'class': 'p-price'})
    #print(prices)
    names = soup.find_all('div', {'class': 'p-name p-name-type-2'})

    products = []
    for name, price in zip(names, prices):
        price = price.text.strip().split('\n')[0]
        price = float(price.replace('￥', ''))
        product = {"name": name.text.strip(), "price": price}
        products.append(product)
        if limit is not None and len(products) == limit:
            break

    driver.quit()

    return products


if __name__ == "__main__":
    url = 'https://passport.jd.com/new/login.aspx'
    if not os.path.isfile('cookies/jd.pkl'):
        print('Cookie not detected, please login so save cookies')
        get_cookies(url, cookies_name='jd')
    products_info = get_product_info_jd('kinder bueno')
    print(products_info)
