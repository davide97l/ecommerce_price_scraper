# E-commerce Price Scraper

This project consists of a multifunctional tool designed to scrape the prices of a set of products from different vendors via e-commerce websites such as Taobao, Tmall, and Jingdong.
The primary function is to compare the scraped prices and identify discounted offers to assist users in finding the best deals for their desired products.

## Example

We have a list of products, for instance: `"Danish Crown Ham Slices 800g"`, `"Danish Crown Barbecue Pork 500g"`, `"Danish Crown Sauce Pork Ribs 200g"`.
These keywords are used to search the e-commerce websites.

The goal is to generate a CSV file that contains the URL of the vendor, the price, and a boolean indicating whether the price is lower than the market price. 

![Project Screenshot](images/result.png)

The market price is given as a CSV file sourced from the official vendor of the products, for instance, Danish Crown.

![Project Screenshot](images/products_list.png)

## Installing and run

A step by step series of examples that tell you how to get a development environment running:

1. Clone the repo
```sh
git https://github.com/davide97l/merchants_price_scraper
```

2. Install Python packages
```sh
pip install -r requirements.txt
```

3. Run
```sh
python main.py --platforms jd taobao tmall
```

## Challenges and Solutions

During the development of this project, I faced several technical obstacles, and here's how I addressed them:

- **Platform Authentication:** Most platforms require user authentication for product scraping. To tackle this, the program is designed to authenticate only once during the first execution, after which the session cookies are saved and reused for subsequent sessions.

- **Bot Detection:** E-commerce platforms employ various measures to identify and block bots. To overcome this, the program incorporates several methods to simulate human-like behavior:
    - **Randomized Requests:** The program generates random user-agents and introduces random intervals between each request to avoid pattern detection.
    - **Captcha Alert:** The program alerts the user when a captcha appears, allowing for manual resolution.
    - **Stealth Scraping:** Used stealth scraping libraries such as [playwright-stealth](https://pypi.org/project/playwright-stealth/) to further enhance the human-like browsing behavior.
    - **Rotating proxy IP:** TODO.

- **Product Matching:** Frequently, the products retrieved may have slightly different names compared to the searched product. To address this issue, the program leverages a Language Model to verify the similarity between the scraped product name and the searched product name. This approach aids in filtering out false positives, ensuring only relevant product data is considered.

These strategies help ensure successful and uninterrupted scraping of product data from e-commerce websites.

## Support this project

If you found this project interesting please support me by giving it a ⭐, I would really appreciate it 😀