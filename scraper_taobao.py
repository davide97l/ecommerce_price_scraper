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


class TaobaoScraper(BaseScraper):
    def __init__(self, products_limit=10, sleep_time=0):
        super().__init__(products_limit, sleep_time)
        self.cookies_path = 'cookies/taobao.pkl'
        self.cookies_name = 'taobao'
        self.url = 'https://www.taobao.com/'
        self.login_url = self.url
        self.store_name = 'taobao'

    def scrape_product_info(self, product_name, headless=False):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://s.taobao.com/search?page=1&q={product_name}&tab=all"

        driver = self.login(headless=headless)
        driver.get(search_url)
        soup = BeautifulSoup(driver.page_source, 'lxml')

        def criteria(tag):
            return tag.find(class_='Price--priceInt--ZlsSi_M') and tag.find(class_='Title--title--jCOPvpf') \
                   and tag.find(class_='Card--mainPicAndDesc--wvcDXaK') \
                   and not tag.find(class_='Card--doubleCard--wznk5U4') and not tag.find(class_='Card--doubleCardWrapper--L2XFE73')
                   #and not tag.find(class_='Title--iconPic--kYJcAc0')

        divs = soup.find_all(criteria)

        def criteria(tag):
            return tag.name == 'a' and tag.get('class') and 'Card--doubleCardWrapper--L2XFE73' in tag.get('class') \
                   #and not tag.find(class_='Title--iconPic--kYJcAc0')

        a_tags = soup.find_all(criteria)
        urls = [a['href'] for a in a_tags]

        products = []
        for div, url in zip(divs, urls):
            is_tmall = div.select_one('.Title--iconPic--kYJcAc0')
            price_int = div.select_one('.Price--priceInt--ZlsSi_M')
            price_float = div.select_one('.Price--priceFloat--h2RR0RK')
            name = div.select_one('.Title--title--jCOPvpf')
            merchant = div.select_one('.ShopInfo--shopName--rg6mGmy')
            price = int(price_int.text.strip()) + float(price_float.text.strip())
            if not url.startswith('https:'):
                url = 'https:' + url
            product = {"product_name": name.text.strip(), "price": price, "merchant": merchant.text.strip(), "url": url,
                       'platform': self.store_name if is_tmall is None else 'tmall'}
            products.append(product)
            if len(products) == self.limit:
                break

        driver.quit()

        return products

    def scrape_product_info_by_weight(self, product_name, use_gpt=False, verbose=False, headless=False):
        product_name_original = product_name.lower().replace(' ', '%20')
        weight_original, product_name_no_w = self.get_weight_from_product_name(product_name_original)
        if weight_original is None:
            print('Error: weight is not specified in product name')
            return
        products_info = self.scrape_product_info(product_name_original, headless=headless)
        ordered_products, scores = self.get_best_matching_product(product_name_original, products_info)
        ordered_products = [product for product, score in zip(ordered_products, scores) if score > 0]
        if verbose: print(ordered_products)
        if verbose: print(scores)
        #products_info = {'product_name': '丹麦皇冠西班牙风味香肠500g图林根风味猪肉肠幕尼黑风味白肠烤肠', 'price': 31.8, 'merchant': '你我的奶酪', 'url': 'https://item.taobao.com/item.htm?abbucket=17&id=760607768121&ns=1'}
        #products_info = {'product_name': '丹麦皇冠纯香肉肠台式火山石烤肠地道肠慕尼黑白肠图林根风味肠', 'price': 49.0, 'merchant': '寻味干货专营店', 'url': 'https://detail.tmall.com/item.htm?id=708213694390&ns=1&abbucket=17'}
        #products_info = {'product_name': '丹麦皇冠图林根香肠德国风味白肉肠熏煮肠西餐简餐商用800g约16条', 'price': 56.9, 'merchant': '瑞瀛生鲜冻品商城', 'url': 'https://detail.tmall.com/item.htm?ali_refid=a3_430582_1006:1684428020:N:TwvSVFUPtXbr29G34LcrOYtomUjWCyWz:3ff52cc43c1d158bc2a9e5f92eac4a77&ali_trackid=100_3ff52cc43c1d158bc2a9e5f92eac4a77&id=753462867032&spm=a21n57.1.0.0'}

        driver = self.login(headless=headless)
        product_dict = []
        for product_info in ordered_products:
            self.sleep()
            driver.get(product_info['url'])
            try:
                element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'skuItemWrapper')))
            except TimeoutException:
                pass  # this will simply cause products_list to be empty which is ok
            soup = BeautifulSoup(driver.page_source, 'lxml')
            #print(soup)

            products_list = soup.select('.skuItem')
            if verbose: print(f'Scraping product {product_info["product_name"]}')
            if verbose: print(f'Scraped {len(products_list)} items in details page')
            if len(products_list) < 2:
                if weight_original not in product_info['product_name']:
                    continue
                score = self.check_name_matching_score(product_name_no_w, product_info['product_name'],
                                                       remove_punctuation=True)
                if score < 1:
                    continue
                product_dict.append({'product_name': product_info['product_name'], 'price': product_info['price'],
                                     'merchant': product_info['merchant'], 'url': product_info['url'],
                                     'platform': self.store_name,
                                     'score': score})
                if verbose: print(product_dict[-1])
                continue

            for i, product in enumerate(products_list):
                self.sleep()
                if 'disabled' in product:  # filter disabled elements
                    continue
                product_name_detail_original = product.text.strip()
                if verbose: print(product_name_detail_original)
                if weight_original not in product_name_detail_original and weight_original not in product_info['product_name']:
                    continue
                weight, product_name_detail = self.get_weight_from_product_name(product_name_detail_original)
                if weight and weight != weight_original:
                    continue
                elif not weight and weight_original not in product_info['product_name']:
                    continue
                score = self.check_name_matching_score(product_name_no_w, product_name_detail, remove_punctuation=True)
                if score < 1:
                    continue
                # now click on it to get the price
                element = driver.find_elements(By.CSS_SELECTOR, '.skuIcon')[i]
                try:
                    element.click()
                except:
                    if verbose: print('Failed to click on page')
                    continue
                # check for discounts
                try:
                    price_element = driver.find_element(By.CLASS_NAME, 'Price--extraPriceText--2dbLkGw')
                except:
                    price_element = driver.find_element(By.CLASS_NAME, 'Price--priceText--2nLbVda')
                if len(price_element.text) < 1:
                    if verbose: print('Could not find price')
                    continue
                price = float(price_element.text)
                product_dict.append({'product_name': f"{product_info['product_name']}-{product_name_detail_original}",
                                     'price': price,
                                     'merchant': product_info['merchant'], 'url': product_info['url'],
                                     'platform': self.store_name,
                                     'score': score})
                if verbose: print(product_dict[-1])

        if len(product_dict) < 2:
            driver.quit()
            if verbose: print('Final result:', product_dict)
            return product_dict
        product_dict = sorted(product_dict, key=lambda x: x['score'], reverse=True)

        # filter with chatgpt
        if use_gpt:
            gpt_scores = [self.check_name_matching_gpt(product['product_name'].split('-')[-1], product_name_original) for product in product_dict]
            gpt_product_dict = [product for i, product in enumerate(product_dict) if gpt_scores[i]]
            if verbose: print('GPT scores:', gpt_scores)
            if verbose: print(f'After GPT filter ({len(gpt_product_dict)}):', product_dict)
            if len(gpt_product_dict) > 0:
                product_dict = gpt_product_dict
        else:
            highest_score = product_dict[0]['score']
            product_dict = [entry for entry in product_dict if entry['score'] == highest_score]

        if verbose: print('Final result:', product_dict)

        driver.quit()

        return product_dict


def test_scraper():
    scraper = TaobaoScraper(products_limit=10)
    products = [#'丹麦皇冠慕尼黑风味白肠500g','丹麦皇冠慕尼黑风味白肠800g', '丹麦皇冠慕尼黑风味白肠350g',
                #'丹麦皇冠图林根风味香肠350g', '丹麦皇冠图林根风味香肠500g', '丹麦皇冠图林根风味香肠800g',
                '丹麦皇冠西班牙风味香肠500g', '丹麦皇冠西班牙风味香肠350g', '丹麦皇冠西班牙风味香肠800g',
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
    '''for i, p in enumerate(products):
        print(f'Scraping product: {products[i]}')
        product_info = scraper.scrape_product_info_by_weight(p, use_gpt=False, verbose=True, headless=False)
        print(f'Target price: {prices[i]}')
        print('--------------------')
        time.sleep(5)'''


if __name__ == "__main__":
    test_scraper()
