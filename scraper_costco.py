import requests
from bs4 import BeautifulSoup


def get_product_info_costco(product_name, limit=10):
    # URL where the search form will redirect (Post action URL)
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
        if limit is not None and len(products) == limit:
            break
    return products


if __name__ == "__main__":
    products_info = get_product_info_costco("kinder bueno")
    print(products_info)
