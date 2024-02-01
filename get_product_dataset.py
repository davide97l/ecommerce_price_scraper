import os
from scraper_costco import CostcoScraper
from scraper_tmall import TmallScraper
from scraper_jd import JDScraper
from scraper_taobao import TaobaoScraper
import pandas as pd
import datetime


if __name__ == "__main__":
    product_name = 'kinder bueno'
    save_dir = 'results'
    vendors = [TaobaoScraper(), TmallScraper(), JDScraper()]
    catalogs = []
    for vendor in vendors:
        try:
            df = vendor.get_product_df(product_name)
            catalogs.append(df)
        except:
            print(f'Scraping failed for vendor: {vendor.store_name}')

    df = pd.concat(catalogs)
    df = df[['vendor', 'name', 'price']]
    df = df.reset_index(drop=True)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M")
    df_path = os.path.join(save_dir, f'catalog_{timestamp}.csv')
    df.to_csv(df_path, index=False)
    print(f'Catalog saved to {df_path}')
    print(df.head(30))
