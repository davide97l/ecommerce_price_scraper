import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from utils import get_cookies
import os
import pickle


def get_product_info_taobao(product_name, cookies='cookies/taobao.pkl', limit=10):
    product_name = product_name.lower().replace(' ', '%20')
    search_url = f"https://s.taobao.com/search?page=1&q={product_name}&tab=all"

    driver = webdriver.Chrome()
    driver.get('https://www.taobao.com')
    cookies = pickle.load(open(cookies, 'rb'))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

    driver.get(search_url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    #print(soup)

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
        if limit is not None and len(products) == limit:
            break

    driver.quit()

    return products


if __name__ == "__main__":
    url = 'https://www.taobao.com/'
    if not os.path.isfile('cookies/taobao.pkl'):
        print('Cookie not detected, please login so save cookies')
        get_cookies(url, cookies_name='taobao')
    products_info = get_product_info_taobao('kinder bueno')
    print(products_info)
