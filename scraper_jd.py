from bs4 import BeautifulSoup
from selenium import webdriver
import pickle
import os
from scraper_base import BaseScraper
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from playwright_stealth import stealth_sync
from playwright.sync_api import sync_playwright
import asyncio


class JDScraper(BaseScraper):
    def __init__(self, products_limit=10, sleep_time=0):
        super().__init__(products_limit, sleep_time)
        self.cookies_path = 'cookies/jd.pkl'
        self.cookies_name = 'jd'
        self.url = 'https://www.jd.com'
        self.login_url = 'https://passport.jd.com/new/login.aspx'
        self.store_name = 'jd'

    def scrape_product_info(self, product_name, headless=False, verbose=True):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://search.jd.com/Search?keyword={product_name}"
        if verbose: print(search_url)

        with sync_playwright() as playwright:
            browser, context = self.login(playwright=playwright)

            # Open new page
            page = context.new_page()
            stealth_sync(page)
            page.goto(search_url)

            products = []
            items = page.query_selector_all('.gl-item')
            for item in items:
                name = item.query_selector('.p-name').inner_text()
                price = item.query_selector('.price-pingou')
                if price is None:
                    price = item.query_selector('.p-price').inner_text()
                else:
                    price = price.inner_text().split('\n')[0]
                price = float(price.replace('￥', ''))
                try:
                    merchant = item.query_selector('.p-shop').text_content()
                except:
                    continue
                url = item.query_selector('.p-img a').get_attribute('href')
                if not url.startswith('https:'):
                    url = 'https:' + url
                product = {"product_name": name.strip(), "price": price, "merchant": merchant.strip(), "url": url,
                           'platform': self.store_name}
                products.append(product)
                if self.limit is not None and len(products) == self.limit:
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
        ordered_products = [product for product, score in zip(ordered_products, scores) if score > 0]
        if verbose: print(ordered_products)
        if verbose: print(scores)

        #ordered_products = [{'product_name': '桃西村原切烟熏专用配菜肉家用 慕尼黑风味白肠800g', 'price': 142.0, 'merchant': '鲨齿猪肉店', 'url': 'https://item.jd.com/10086095812629.html'}]

        with sync_playwright() as playwright:
            browser, context = self.login(playwright=playwright)

            # Open new page
            page = context.new_page()
            stealth_sync(page)
            page.goto(self.url)
            if "验证一下，购物无忧" in page.content():
                print('Captcha detected!')
                exit()
            #print(page.content())

            product_dict = []
            for product_info in ordered_products:
                self.sleep()
                page.goto(product_info['url'])
                if "验证一下，购物无忧" in page.content():
                    print('Captcha detected!')
                    exit()

                '''try:
                    element = page.wait_for_selector('.item', timeout=5000)
                except asyncio.TimeoutError:
                    pass  # this will simply cause products_list to be empty which is ok'''

                products_list = page.query_selector_all('.item[data-sku]')
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
                    # can check price of disabled elements
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
                    sku_icons = page.query_selector_all('.item[data-sku]')
                    try:
                        sku_icons[i].click()
                    except:
                        if verbose: print('Failed to click on page')
                        continue
                    j = 10
                    while j > 0:  # 10 attempts to retrieve the price
                        try:
                            price_element = page.query_selector('.price')
                            if price_element is not None and len(price_element.text_content()) > 0:
                                break
                            if "验证一下，购物无忧" in page.content():
                                print('Captcha detected!')
                                exit()
                        except:
                            pass
                        page.reload()
                        self.sleep()
                        j -= 1
                    if j == 0:
                        if verbose: print(f'skipped element due to price not found')
                        continue

                    # check for discounts
                    price_element = page.query_selector('.price')
                    if price_element is None or len(price_element.text_content()) < 1:
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
    scraper = JDScraper(products_limit=10, sleep_time=1)
    products = [
        '丹麦皇冠慕尼黑风味白肠500g',
        '丹麦皇冠慕尼黑风味白肠800g',
    ]
    prices = [
        71.5, 142
    ]
    for i, p in enumerate(products):
        print(f'Scraping product: {products[i]}')
        product_info = scraper.scrape_product_info_by_weight(p, use_gpt=False, verbose=True, headless=False)
        print(f'Target price: {prices[i]}')
        print('--------------------')
        time.sleep(5)


if __name__ == "__main__":
    test_scraper()