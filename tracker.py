import time
import sys
import json
import traceback

from pprint import pprint

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def save_prices(prices):
    with open('prices.json', 'w') as f:
        json.dump(prices, f)

def load_prices():
    try:
        with open('prices.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_products():
    with open('products.txt') as f:
        products = f.readlines()
    return products

def get_prices(products):
    res = {}

    # Set up options for the driver
    options = Options()
    options.headless = True

    # Set the path to the geckodriver executable
    #gecko_path = r'S:\GitHub\takealot-price-tracker\geckodriver-v0.33.0-win64\geckodriver.exe'

    # Initialize the driver
    #driver = webdriver.Firefox(executable_path=gecko_path, options=options)
    driver = webdriver.Firefox(options=options)
    try:
        for url in products:
            url = url.strip()
            if not url:
                continue

            # navigate to a page
#            url = "https://www.takealot.com/xiaomi-redmi-9t-128gb-carbon-grey/PLID72013248"
            print(url)
            driver.get(url)

            # Wait until the 'div.sf-buybox' element is loaded
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.sf-buybox')))

            # retrieve text

        #    print(driver)
        #    print(dir(driver))

        #    element_text = driver.find_element_by_tag_name('body').text

        # <span class="currency plus currency-module_currency_29IIm" data-ref="buybox-price-main">R 4,250</span>

#            element = driver.find_element(By.CSS_SELECTOR ,'span.currency.plus.currency-module_currency_29IIm')    
#            element = driver.find_element(By.XPATH,'//*[@id="shopfront-app"]/div[4]/div[1]/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div[1]/span')  

#            time.sleep(1)
            element = driver.find_element(By.CSS_SELECTOR,'div.sf-buybox')

            # Extract the prices from the element's text
            prices = [price for price in element.text.split('\n') if price.startswith('R')]
#            price = price_line.split()[0]  # Get the first word in the line (the price)
#            print(price)

            pprint(prices)

#            elements = driver.find_elements(By.CSS_SELECTOR,'span.currency.plus')
#            for element in elements:
#                print(element.text)

#            price = element.text
#            print(price)
#            assert price.startswith('R')   

            assert len(prices) > 0

            res[url] = prices

#            sys.exit(1)

        return res
    
    finally:
        # close the browser
        driver.quit()


def main():
    products = load_products()
    prices_now = get_prices(products)
  
#    print(prices_now)

    PRICES = load_prices()

    new_price = False
    for url, prices in prices_now.items():
        if url not in PRICES:
            PRICES[url] = []

        for price in prices:
            if price not in PRICES[url]:  # Avoid adding duplicate prices
                new_price = True
                print(url, '-', price)
                PRICES[url].append(price)

    save_prices(PRICES)

    return new_price

if __name__ == '__main__':
    try:
        res=main()
        if res:
            input('New price found!\nPress enter to exit...')
    except:
        traceback.print_exc()  # This will print the full stack trace
        input('Press enter to exit...')
