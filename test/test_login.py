from playwright.sync_api import sync_playwright
import requests
import os
import pickle


from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    with open('../cookies/taobao.pkl', 'rb') as f:
        cookies = pickle.load(f)
    context.add_cookies(cookies)

    # Open new page
    page = context.new_page()

    # Go to url
    page.goto('https://s.taobao.com/search?fromTmallRedirect=true&page=1&q=丹麦皇冠木烟熏蒸煮香肠200g&tab=mall')

    source_code = page.content()
    print(source_code)


    # Scrape data here
    # This is just an example, adjust selectors and logic based on what you need
    items = page.query_selector_all('.Card--doubleCardWrapperMall--uPmo5Bz')
    print(items)
    for item in items:
        title_element = item.query_selector('.Title--title--jCOPvpf')
        if title_element:  # Check if the element was found
            title = title_element.text_content()
            print(f'Title: {title}')

    # Close page and browser
    page.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)

#url = 'https://www.taobao.com/'
#login(url, '../cookies/taobao.pkl')