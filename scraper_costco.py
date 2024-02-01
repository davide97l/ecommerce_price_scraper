from bs4 import BeautifulSoup
from selenium import webdriver
import pickle
import os
import requests
from scraper_base import BaseScraper


class CostcoScraper(BaseScraper):
    def __init__(self, products_limit=10):
        super().__init__(products_limit)
        self.store_name = 'costco'

    def scrape_product_info(self, product_name):

        product_name = product_name.lower().replace(' ', '+')
        search_url = f"https://www.costco.com/CatalogSearch?dept=All&keyword={product_name}"

        headers = {'User-Agent': 'Mozilla/5.0'}   # Provide User-Agent

        response = requests.get(search_url, headers=headers)

        soup = BeautifulSoup(response.text, 'lxml')

        prices = soup.select('div.price')
        names = soup.select('span.description')
        products = []
        for name, price in zip(names, prices):
            price = price.text.strip()
            price = float(price.replace('$', ''))
            product = {"name": name.text.strip(), "price": price}
            products.append(product)
            if self.limit is not None and len(products) == self.limit:
                break
        return products

    def get_product_info(self, product_name):
        products_info = self.scrape_product_info(product_name)
        return products_info
