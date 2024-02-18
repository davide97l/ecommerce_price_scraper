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
from playwright.sync_api import sync_playwright
import asyncio
from playwright_stealth import stealth_sync


class TaobaoScraper(BaseScraper):
    def __init__(self, products_limit=10, sleep_time=0):
        super().__init__(products_limit, sleep_time)
        self.cookies_path = 'cookies/taobao.pkl'
        self.cookies_name = 'taobao'
        self.url = 'https://www.taobao.com/'
        self.login_url = self.url
        self.store_name = 'taobao'

    def scrape_product_info(self, product_name, headless=False, verbose=True):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://s.taobao.com/search?page=1&q={product_name}"
        if verbose: print(search_url)

        with sync_playwright() as playwright:
            browser, context = self.login(playwright=playwright)

            # Open new page
            page = context.new_page()
            stealth_sync(page)
            page.goto(search_url)
            source_code = page.content()
            #print(source_code)

            products = []
            items = page.query_selector_all('.Card--doubleCardWrapper--L2XFE73')
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

    def scrape_product_info_by_weight(self, product_name, use_gpt=False, verbose=False, headless=False):
        product_name_original = product_name.lower().replace(' ', '%20')
        weight_original, product_name_no_w = self.get_weight_from_product_name(product_name_original)
        if weight_original is None:
            print('Error: weight is not specified in product name')
            return
        products_info = self.scrape_product_info(product_name_original, headless=headless)
        if len(products_info) == 0:
            print('Possible captcha detected!')
            exit()
        ordered_products, scores = self.get_best_matching_product(product_name_original, products_info)
        # keep the vendors with positive score
        ordered_products = [product for product, score in zip(ordered_products, scores) if score > 0]
        if verbose: print(ordered_products)
        if verbose: print(scores)
        #ordered_products = [{'product_name': '丹麦皇冠慕尼黑风味白肠500g', 'price': 56.9, 'merchant': '瑞瀛生鲜冻品商城', 'url': 'https://item.taobao.com/item.htm?abbucket=19&id=760607768121&ns=1&spm=a21n57.1.0.0.777a523c2PlHCJ'}]

        with sync_playwright() as playwright:
            browser, context = self.login(playwright=playwright)

            # Open new page
            page = context.new_page()
            page.goto(self.url)
            if "Please slide to verify" in page.content():
                print('Captcha detected!')
                exit()
            #print(page.content())

            product_dict = []
            for product_info in ordered_products:
                self.sleep()
                page.goto(product_info['url'])
                if "Please slide to verify" in page.content():
                    print('Captcha detected!')
                    exit()

                try:
                    element = page.wait_for_selector('.skuItemWrapper', timeout=5000)
                except asyncio.TimeoutError:
                    pass  # this will simply cause products_list to be empty which is ok

                products_list = page.query_selector_all('.skuItem')
                if verbose: print(f'Scraping product {product_info["product_name"]}')
                if verbose: print(f'Scraped {len(products_list)} items in details page')

                # case ho products in details page
                if len(products_list) < 2:
                    if weight_original not in product_info['product_name']:
                        continue
                    score = self.check_name_matching_score(product_name, product_info['product_name'],
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
                    if 'disabled' in product.get_attribute('class'):
                        continue
                    product_name_detail_original = product.text_content().strip()
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
                    sku_icons = page.query_selector_all('.skuIcon')
                    try:
                        sku_icons[i].click()
                    except:
                        if verbose: print('Failed to click on page')
                        continue
                    # check for discounts
                    price_element = page.query_selector('.Price--extraPriceText--2dbLkGw')
                    if price_element is None:
                        price_element = page.query_selector('.Price--priceText--2nLbVda')

                    if len(price_element.text_content()) < 1:
                        if verbose: print('Could not find price')
                        continue
                    price = float(price_element.text_content())
                    product_dict.append({'product_name': f"{product_info['product_name']}-{product_name_detail_original}",
                                         'price': price,
                                         'merchant': product_info['merchant'], 'url': product_info['url'],
                                         'platform': self.store_name,
                                         'score': score})
                    if verbose: print(product_dict[-1])

            if len(product_dict) < 2:
                page.close()
                browser.close()
                if verbose: print('Final result:', product_dict)
                if len(product_dict) == 0:
                    if verbose: print('No results found')
                return product_dict

            product_dict = sorted(product_dict, key=lambda x: x['score'], reverse=True)

            # filter with chatgpt
            if use_gpt:
                gpt_scores = [self.check_name_matching_gpt(product['product_name'].split('-')[-1], product_name_original) for product in product_dict]
                gpt_product_dict = [product for i, product in enumerate(product_dict) if gpt_scores[i]]
                if verbose: print('GPT scores:', gpt_scores)
                if verbose: print(f'Before GPT filter ({len(product_dict)}):', product_dict)
                if verbose: print(f'After GPT filter ({len(gpt_product_dict)}):', gpt_product_dict)
                if len(gpt_product_dict) > 0:
                    product_dict = gpt_product_dict
            else:
                highest_score = product_dict[0]['score']
                product_dict = [entry for entry in product_dict if entry['score'] == highest_score]

            if verbose: print('Final result:', product_dict)

            page.close()
            browser.close()

        return product_dict


def test_scraper():
    scraper = TaobaoScraper(products_limit=10, sleep_time=1)
    products = [#'丹麦皇冠木烟熏蒸煮香肠200g'
                '丹麦皇冠慕尼黑风味白肠500g',
                #'丹麦皇冠慕尼黑风味白肠800g', '丹麦皇冠慕尼黑风味白肠350g',
                #'丹麦皇冠图林根风味香肠350g', '丹麦皇冠图林根风味香肠500g', '丹麦皇冠图林根风味香肠800g',
                #'丹麦皇冠西班牙风味香肠500g', '丹麦皇冠西班牙风味香肠350g', '丹麦皇冠西班牙风味香肠800g',
                #'丹麦皇冠木烟熏蒸煮香肠200g', '丹麦皇冠木烟熏蒸煮香肠1kg',
                #'丹麦皇冠木烟熏蒸煮热狗肠200g', '丹麦皇冠木烟熏蒸煮热狗肠1kg', '丹麦皇冠超值热狗肠200g', '丹麦皇冠超值热狗肠1kg'
                ]
    prices = [
        49, 64, 32,
        31.8, 49, 49,
        52, 27.84, 60
    ]
    for i, p in enumerate(products):
        print(f'Scraping product: {products[i]}')
        product_info = scraper.scrape_product_info_by_weight(p, use_gpt=True, verbose=True, headless=True)
        print(f'Target price: {prices[i]}')
        print('--------------------')
        time.sleep(5)


if __name__ == "__main__":
    test_scraper()
