import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import random
from utils import get_cookies
import os
import pickle


def get_product_info_tmall(product_name, cookies='cookies/taobao.pkl', limit=10):
    product_name = product_name.lower().replace(' ', '%20')
    search_url = f"https://s.taobao.com/search?fromTmallRedirect=true&q={product_name}&tab=mall"

    driver = webdriver.Chrome()
    driver.get('https://www.taobao.com')
    cookies = pickle.load(open(cookies, 'rb'))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

    driver.get(search_url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    #print(soup)

    prices_int = soup.select('.Price--priceInt--ZlsSi_M')
    prices_float = soup.select('.Price--priceFloat--h2RR0RK')
    names = soup.select('.Title--title--jCOPvpf')

    products = []
    for name, price_int, price_float in zip(names, prices_int, prices_float):
        price = int(price_int.text.strip()) + float(price_float.text.strip())
        product = {"name": name.text.strip(), "price": price}
        products.append(product)
        if limit is not None and len(products) == limit:
            break

    driver.quit()

    return products


# https://blog.csdn.net/qq_37626867/article/details/111084756
# kept as reference but not working due to captcha
def taobao_login(username, password):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    default_url = 'https://www.taobao.com/'
    driver.get(default_url)
    wait = WebDriverWait(driver, 3)

    sleep(random.uniform(2.0, 3.0))
    loginElement = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, '亲，请登录')))
    loginElement.click()

    sleep(random.uniform(2.0, 3.0))
    login_name = wait.until(EC.presence_of_element_located((By.NAME, 'fm-login-id')))
    login_name.send_keys(username)

    sleep(random.uniform(2.0, 3.0))
    login_password = wait.until(EC.presence_of_element_located((By.NAME, 'fm-login-password')))
    login_password.send_keys(password)

    sleep(random.uniform(2.0, 3.0))
    login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'fm-btn')))
    login_button.click()

    print('Login successful')


if __name__ == "__main__":
    url = 'https://www.taobao.com/'
    if not os.path.isfile('cookies/taobao.pkl'):
        print('Cookie not detected, please login so save cookies')
        get_cookies(url, cookies_name='taobao')
    #taobao_login()
    products_info = get_product_info_tmall('kinder bueno')
    print(products_info)
