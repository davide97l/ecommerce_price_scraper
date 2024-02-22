import os
from scraper_jd import JDScraper
from scraper_taobao import TaobaoScraper
from scraper_tmall import TmallScraper
import pandas as pd
import datetime
import argparse


def process_dataset(df, promo_price, product_name):
    df = df[['platform', 'merchant', 'product_name', 'price', 'url']]
    df = df.reset_index(drop=True)
    df['price'] = df['price'].astype(float)
    df['promo_price'] = float(promo_price)
    df['searched_product'] = str(product_name)
    df['is_under_promo_price'] = df['price'].apply(lambda x: True if x < float(promo_price) else False)
    df = df.drop_duplicates(subset='merchant', keep='first')
    return df


def main(prefix, sleep_time, headless, platforms):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d")
    save_dir = f'results/{timestamp}'

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    platform_classes = {'jd': JDScraper, 'taobao': TaobaoScraper, 'tmall': TmallScraper}
    platforms = [platform_classes[p](sleep_time=sleep_time, products_limit=5) for p in platforms]

    # load df catalog and get products list and promo prices
    xl = pd.ExcelFile('inputs/catalog.xlsx')
    df = xl.parse('规格-概览（總表）')
    promo_prices = df.iloc[:, 10].dropna().tolist()[1:]
    product_names = df.iloc[:, 3].dropna().tolist()
    catalog = pd.DataFrame({
        'product_names': df.iloc[:, 3],
        'promo_prices': df.iloc[:, 10]
    }).dropna()
    print(catalog)

    tot_products = len(product_names)
    i = 0
    for product_name, promo_price in zip(product_names, promo_prices):
        if not product_name.startswith(prefix):
            product_name = prefix + product_name
        for platform in platforms:
            print(f'Scraping product : {product_name} ({i+1}/{tot_products}) from {platform.store_name}')
            df_path = os.path.join(save_dir, f'{product_name}_{platform.store_name}.csv')
            empty_df_path = os.path.join(save_dir, f'empty_{product_name}_{platform.store_name}.csv')
            if os.path.isfile(df_path) or os.path.isfile(empty_df_path):
                print(f"{df_path} already scraped")
                continue
            product_dict = platform.scrape_product_info_by_weight(
                product_name, use_gpt=1, verbose=1, headless=headless)
            if len(product_dict) == 0:
                print(f'No suitable items found for {product_name}')
                df = pd.DataFrame()
                df_path = empty_df_path
            else:
                df = pd.DataFrame(product_dict)
                df = process_dataset(df, promo_price, product_name)
            df.to_csv(df_path, index=False)
            print(f'Product catalog saved to {df_path}')
        i += 1

    df_list = []
    for filename in os.listdir(save_dir):
        if filename.endswith('.csv') and not filename.endswith('full_catalog.csv') and not 'empty' in filename:
            file_path = os.path.join(save_dir, filename)
            df = pd.read_csv(file_path)
            df_list.append(df)
    full_df = pd.concat(df_list, ignore_index=True)
    df_path = os.path.join(save_dir, 'full_catalog.csv')
    full_df.to_csv(df_path, index=False)
    print(f'Full catalog saved to {df_path}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--prefix', type=str, default='丹麦皇冠', help='Prefix for the product name, usually the brand of the product, can also leave empty here')
    parser.add_argument('--sleep_time', type=float, default=5.0, help='Sleep time for the scraper')
    parser.add_argument('--headless', type=bool, default=False, help='Whether to run the scraper in headless mode')
    parser.add_argument('--platforms', nargs='+', default=['jd'], help='List of platforms to use')

    args = parser.parse_args()
    main(args.prefix, args.sleep_time, args.headless, args.platforms)
