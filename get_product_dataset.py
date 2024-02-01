from scraper_costco import CostcoScraper
from scraper_tmall import TmallScraper
from scraper_jd import JDScraper
from scraper_taobao import TaobaoScraper
import pandas as pd


if __name__ == "__main__":

    product_name = 'kinder bueno'
    vendors = [TaobaoScraper(), TmallScraper(), JDScraper()]
    catalogs = [vendor.get_product_df(product_name) for vendor in vendors]  # TODO try ang except

    df = pd.concat(catalogs)
    df = df[['vendor', 'name', 'price']]  # TODO fix dataset

    print(df)
