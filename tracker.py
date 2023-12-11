import time
import sys
import json
import traceback
import colorama

from colorama import Fore, Back, Style
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

            if url.startswith('###'):
                break

            if url.startswith('#'):
                continue

            # navigate to a page
#            url = "https://www.takealot.com/xiaomi-redmi-9t-128gb-carbon-grey/PLID72013248"
            print(url)
            driver.get(url)

            # Wait until the 'div.sf-buybox' element is loaded
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.sf-buybox')))
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.stock-availability-status')))            
            time.sleep(2)

            # retrieve text

            # <span class="currency plus currency-module_currency_29IIm" data-ref="buybox-price-main">R 4,250</span>
            element = driver.find_element(By.CSS_SELECTOR,'div.sf-buybox')

            # Extract the prices from the element's text
            prices = [price for price in element.text.split('\n') if price.startswith('R')]
            assert len(prices) > 0

            # <div class="cell shrink stock-availability-status" data-ref="stock-availability-status"><span>In stock</span></div>
            element = driver.find_element(By.CSS_SELECTOR,'div.stock-availability-status')
            status = element.text

            # <span class="rounded-pill " data-ref="buybox-only-x-left">Only 20 left</span>
#            warning = driver.find_element(By.CSS_SELECTOR,'span.rounded-pill')
            warnings = driver.find_elements(By.CSS_SELECTOR,'span.rounded-pill')
            if warnings:
                warning = warnings[0].text
            else:
                warning = ''

            if 'out of stock' in status:
                status_color = Style.BRIGHT + Fore.WHITE + Back.RED + status
            elif 'In stock' not in status:
                status_color = Style.BRIGHT + Fore.WHITE + Back.YELLOW + status
            else:
                status_color = Style.BRIGHT + Fore.WHITE + Back.GREEN + status

            print(prices, '-', status_color, '- ' + Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning if warning else "")                     
            print()
            
            res[url] = {'prices':prices, 'status':status,'warning':warning}

#            sys.exit(1)

        return res
    
    finally:
        # close the browser
        driver.quit()


def main():
    colorama.init(autoreset=True)

    products = load_products()

#    products = products[0:1] # TAKE OUT
#    pprint(products)

    prices_now = get_prices(products)
  
#    print(prices_now)
    print('-'*80)

    PRICES = load_prices()

    new_price = False
    for url in prices_now.keys():
        do_price_check = True
        if url not in PRICES: # new item
            PRICES[url] = {'prices':[], 'status':prices_now[url]['status'], 'warning':prices_now[url]['warning']}
            do_price_check = False
        else: # existing item
            PRICES[url]['status'] = prices_now[url]['status']
            PRICES[url]['warning'] = prices_now[url]['warning']

        for price in prices_now[url]['prices']:

            if price not in PRICES[url]['prices']:  # Avoid adding duplicate prices
                PRICES[url]['prices'].append(price)

                if do_price_check:

                    status = PRICES[url]['status']
                    if 'warning' in PRICES[url]:
                        warning = PRICES[url]['warning']
                    else:
                        warning = ''

                    price_now = int(price.replace('R','').replace(',','').strip())
                    prices_clean = [int(p.replace('R','').replace(',','').strip()) for p in PRICES[url]['prices']]

                    price_color = Style.NORMAL
                    if price_now <= min(prices_clean):
                        price_color = Style.BRIGHT + Fore.WHITE + Back.GREEN
                    elif price_now >= max(prices_clean):
                        price_color = Style.BRIGHT + Fore.WHITE + Back.RED
                    else:
                        price_color = Style.BRIGHT + Fore.WHITE + Back.BLUE

                    print(url, '-', end=' ')
                    for p in PRICES[url]['prices']:
                        if p == price:
                            print(price_color + p + Style.RESET_ALL, end=' ')
                        else:
                            print(p, end=' ')

                    if 'out of stock' in status:
                        status_color = Style.BRIGHT + Fore.WHITE + Back.RED + status
                    elif 'In stock' not in status:
                        status_color = Style.BRIGHT + Fore.WHITE + Back.YELLOW + status
                    else:
                        status_color = Style.BRIGHT + Fore.WHITE + Back.GREEN + status

                    print('-', status_color, '- ' + Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning if warning else "")

#                    print(url, '-', ['>' + p + '<' if p == price else p for p in PRICES[url]['prices']], '-', PRICES[url]['status'])
                    new_price = True

    save_prices(PRICES)

    return new_price


if __name__ == '__main__':
    try:
        res=main()
        if res:
            input('New price(s) found!\nPress enter to exit...')
    except:
        traceback.print_exc()  # This will print the full stack trace
        input('Press enter to exit...')
