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


class JDScraper(BaseScraper):
    def __init__(self, products_limit=10, sleep_time=0):
        super().__init__(products_limit, sleep_time)
        self.cookies_path = 'cookies/jd.pkl'
        self.cookies_name = 'jd'
        self.url = 'https://www.jd.com'
        self.login_url = 'https://passport.jd.com/new/login.aspx'
        self.store_name = 'jd'

    def scrape_product_info(self, product_name, headless=False):
        product_name = product_name.lower().replace(' ', '%20')
        search_url = f"https://search.jd.com/Search?keyword={product_name}"

        driver = self.login(headless=headless)
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
            product = {"product_name": name, "price": price, "merchant": merchant.text.strip(), "url": url,
                       'platform': self.store_name}
            products.append(product)
            if self.limit is not None and len(products) == self.limit:
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
        if len(products_info) == 0:
            print('Possible captcha detected!')
            exit()
        #ordered_products = [{'product_name': '桃西村原切烟熏专用配菜肉家用 慕尼黑风味白肠800g', 'price': 142.0, 'merchant': '鲨齿猪肉店', 'url': 'https://item.jd.com/10086095812629.html'}]
        #products_info = {'product_name': '丹麦皇冠纯香肉肠台式火山石烤肠地道肠慕尼黑白肠图林根风味肠', 'price': 49.0, 'merchant': '寻味干货专营店', 'url': 'https://detail.tmall.com/item.htm?id=708213694390&ns=1&abbucket=17'}
        #products_info = {'product_name': '丹麦皇冠图林根香肠德国风味白肉肠熏煮肠西餐简餐商用800g约16条', 'price': 56.9, 'merchant': '瑞瀛生鲜冻品商城', 'url': 'https://detail.tmall.com/item.htm?ali_refid=a3_430582_1006:1684428020:N:TwvSVFUPtXbr29G34LcrOYtomUjWCyWz:3ff52cc43c1d158bc2a9e5f92eac4a77&ali_trackid=100_3ff52cc43c1d158bc2a9e5f92eac4a77&id=753462867032&spm=a21n57.1.0.0'}

        driver = self.login(headless=headless)
        product_dict = []
        for product_info in ordered_products:
            self.sleep()
            driver.get(product_info['url'])
            if "验证一下，购物无忧" in driver.page_source:
                print('Captcha detected!')
                exit()
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'item')))
            except TimeoutException:
                pass  # this will simply cause products_list to be empty which is ok
            soup = BeautifulSoup(driver.page_source, 'lxml')
            #print(soup)

            products_list = soup.select('.item[data-sku]')
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
                #if 'no-stock' in product:  # can check price of disabled elements
                #    continue
                product_name_detail_original = product.text.strip()
                if verbose: print(product_name_detail_original)
                if weight_original not in product_name_detail_original and weight_original not in product_info['product_name']:
                    if verbose: print('weight not specified')
                    continue
                weight, product_name_detail = self.get_weight_from_product_name(product_name_detail_original)
                if weight and weight != weight_original:
                    if verbose: print(f'weights not matching: {weight} and {weight_original}')
                    continue
                elif not weight and weight_original not in product_info['product_name']:
                    continue
                score = self.check_name_matching_score(product_name_no_w, product_name_detail, remove_punctuation=True)
                if score < 1:
                    if verbose: print(f'low match score: {score}')
                    continue
                # now click on it to get the price
                element = driver.find_elements(By.CSS_SELECTOR, '.item[data-sku]')[i]
                try:
                    element.click()
                except:
                    if verbose: print('Failed to click on page')
                    continue
                driver.refresh()
                j = 10
                while j > 0:  # 10 attempts to retrieve the price
                    try:
                        price_element = driver.find_element(By.CLASS_NAME, 'price')
                        if len(price_element.text) > 0:
                            break
                    except:
                        pass
                    driver.refresh()
                    self.sleep()
                    j -= 1
                if j == 0:
                    if verbose: print(f'skipped element due to price not found')
                    continue
                # check price
                price_element = driver.find_element(By.CLASS_NAME, 'price')
                if len(price_element.text) < 1:
                    if verbose: print(f'Could not find price: {price_element.text}')
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

        driver.quit()

        return product_dict


def test_scraper():
    scraper = JDScraper(products_limit=10, sleep_time=1)
    products = [
        '丹麦皇冠慕尼黑风味白肠500g', '丹麦皇冠慕尼黑风味白肠800g', '丹麦皇冠慕尼黑风味白肠350g',
        #'丹麦皇冠图林根风味香肠350g', '丹麦皇冠图林根风味香肠500g', '丹麦皇冠图林根风味香肠800g',
        #'丹麦皇冠西班牙风味香肠500g', '丹麦皇冠西班牙风味香肠350g', '丹麦皇冠西班牙风味香肠800g',
        #'丹麦皇冠木烟熏蒸煮香肠200g', '丹麦皇冠木烟熏蒸煮香肠1kg',
        #'丹麦皇冠木烟熏蒸煮热狗肠200g', '丹麦皇冠木烟熏蒸煮热狗肠1kg', '丹麦皇冠超值热狗肠200g', '丹麦皇冠超值热狗肠1kg'
    ]
    prices = [
        71.5, 142, 39,
        31.8, 49, 49,
        52, 27.84, 60
    ]
    for i, p in enumerate(products):
        print(f'Scraping product: {products[i]}')
        product_info = scraper.scrape_product_info_by_weight(p, use_gpt=False, verbose=True, headless=False)
        print(f'Target price: {prices[i]}')
        print('--------------------')
        time.sleep(5)


if __name__ == "__main__":
    test_scraper()