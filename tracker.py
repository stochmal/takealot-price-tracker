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

def get_status_color(status):
    if 'out of stock' in status:
        return Style.BRIGHT + Fore.WHITE + Back.RED + status
    elif 'In stock' not in status:
        return Style.BRIGHT + Fore.WHITE + Back.YELLOW + status
    else:
        return Style.BRIGHT + Fore.WHITE + Back.GREEN + status

def get_price_color(price_now, prices):

    prices_clean = [int(p.replace('R','').replace(',','').strip()) for p in prices]

    res = ""

    for i,price_ in enumerate(prices):

        price_clean = int(price_.replace('R','').replace(',','').strip())
        price_color = Style.NORMAL
        if price_ == price_now:
            price_color = Style.BRIGHT + Fore.WHITE + Back.BLUE
        elif price_clean <= min(prices_clean):
            price_color = Style.BRIGHT + Fore.WHITE + Back.GREEN
        elif price_clean >= max(prices_clean):
            price_color = Style.BRIGHT + Fore.WHITE + Back.RED
        else:
            price_color = Style.RESET_ALL

        res += price_color + prices[i] + Style.RESET_ALL + ' '

    return res.strip()

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
#            print(url, '-', end=' ')                 
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
            
            print(get_price_color(prices[0], prices), '-', end=' ')

            status_color = get_status_color(status)
            
            print(status_color, '- ' + Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning if warning else "")                     
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

    prices_now = get_prices(products)

    print('-'*37,'alerts','-'*37)

    PRICES_OLD = load_prices()

    got_alert = False
    for url in prices_now.keys():

        status_now = prices_now[url]['status']
        warning_now = prices_now[url]['warning']

        new_item = False
        if url not in PRICES_OLD: # new item

            status_old = ''
            warning_old = ''

            PRICES_OLD[url] = {'prices':[], 'status':status_now, 'warning':warning_now}
            new_item = True
        else: # existing item

            status_old = PRICES_OLD[url]['status']
            warning_old = PRICES_OLD[url]['warning']

            PRICES_OLD[url]['status'] = status_now
            PRICES_OLD[url]['warning'] = warning_now

        price_now = prices_now[url]['prices'][0] # it's always the first price in the list
        new_prices = [price for price in prices_now[url]['prices'] if price not in PRICES_OLD[url]['prices']]

        for new_price in new_prices:
            PRICES_OLD[url]['prices'].append(new_price)

        if not new_item:
            if new_prices or status_old != status_now or warning_old != warning_now: # or back_in_stock:

#                    print(url, '-', end=' ')                    
                print(url)   

#                    print(get_price_color(price_now, PRICES[url]['prices']), '-', end=' ')
                print(get_price_color(price_now, PRICES_OLD[url]['prices']))

                if status_old != status_now:
                    print(get_status_color(status_old), Style.RESET_ALL, '--> ', get_status_color(status_now))
                else:
                    print(get_status_color(status_now))

                if warning_now:    
                    if warning_old != warning_now:
                        print(Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning_old if warning_old else ""
                            , Style.RESET_ALL, '--> ', Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning_now if warning_now else "")                        
                    else:
                        print(Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning_now if warning_now else "")

                print()

                got_alert = True

    save_prices(PRICES_OLD)

    return got_alert


if __name__ == '__main__':
    try:
        res=main()
        if res:
            input('New price(s) found!\nPress enter to exit...')
    except:
        traceback.print_exc()  # This will print the full stack trace
        input('Press enter to exit...')
