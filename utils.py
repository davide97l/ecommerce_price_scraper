from selenium import webdriver
import pickle
import time
import os


def get_cookies(url, login_time=30, cookies_name='cookies', save_dir='cookies'):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    driver = webdriver.Chrome()
    driver.get(url)  # Navigate to your URL

    print(f'Now you have {login_time}s to login')
    time.sleep(login_time)

    # This creates cookies.pkl and saves the cookies:
    cookies_path = os.path.join(save_dir, f"{cookies_name}.pkl")
    pickle.dump(driver.get_cookies(), open(cookies_path, "wb"))
    print(f'Cookies saved at {cookies_path}')

    driver.quit()
