import pandas as pd


def process_dataset(df, product_name, promo_price):
    def check_name_matching(product_vendor):
        if all(char in product_vendor for char in product_name):
            return True
        return False
    df = df[df['product_name'].apply(check_name_matching)]
    df = df.reset_index(drop=True)
    df['price'] = df['price'].astype(float)
    df = df.loc[df.groupby('platform')['price'].idxmin()]
    return df


if __name__ == "__main__":
    product_name = '丹麦慕尼黑白肠500g'
    save_dir = 'results'
    df = pd.read_csv('results/catalog_丹麦慕尼黑白肠_202402021412.csv')
    df = process_dataset(df, product_name)
    print(df)

