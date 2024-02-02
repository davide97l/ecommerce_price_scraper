import os
from scraper_costco import CostcoScraper
from scraper_tmall import TmallScraper
from scraper_jd import JDScraper
from scraper_taobao import TaobaoScraper
import pandas as pd
import datetime
from process_dataset import process_dataset


def scrape_product(product_name, save_dir='results'):
    platforms = [TaobaoScraper(), TmallScraper(), JDScraper()]
    catalogs = []
    for platform in platforms:
        try:
            df = platform.get_product_df(product_name)
            catalogs.append(df)
        except:
            print(f'Scraping failed for vendor: {platform.store_name}')

    df = pd.concat(catalogs)
    df = df[['platform', 'merchant', 'product_name', 'price', 'url']]
    df = df.reset_index(drop=True)

    df_path = os.path.join(save_dir, f'catalog_{product_name.replace(" ", "")}.csv')
    df.to_csv(df_path, index=False)
    print(f'Catalog saved to {df_path}')
    return df


if __name__ == "__main__":
    product_name = '丹麦慕尼黑白肠'
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d")
    save_dir = f'results/{timestamp}'

    # load df catalog and get products list and promo prices
    xl = pd.ExcelFile('inputs/catalog.xlsx')
    df = xl.parse('规格-概览（總表）')
    promo_prices = df.iloc[:, 10].dropna()
    product_names = df.iloc[:, 3].dropna()
    catalog = pd.DataFrame({
        'product_names': df.iloc[:, 3],
        'promo_prices': df.iloc[:, 10]
    }).dropna()
    print(catalog)

    tot_products = len(product_names)
    i = 0
    process_df = []
    for product_name, promo_price in zip(product_names, promo_prices):
        print(f'Scraping product: {product_name} ({i+1}/{tot_products})')
        df = scrape_product(product_name, save_dir)  # scrape product data
        df = process_dataset(df, product_name, promo_price)  # TODO preprocess data
        process_df.append(df)
        i += 1

    df = pd.concat(process_df)
    df = df.reset_index(drop=True)
    df_path = os.path.join(save_dir, f'full_catalog.csv')
    df.to_csv(df_path, index=False)
    print(f'Full catalog saved to {df_path}')

