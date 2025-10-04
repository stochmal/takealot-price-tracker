import time
import sys
import json
import traceback
import colorama
import selenium
from datetime import datetime

from colorama import Fore, Back, Style
from pprint import pprint

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from typing import Dict, List, Tuple, Optional, Any, Callable


OUT_OF_STOCK = 'Out of stock'
IN_STOCK = 'In stock'

def save_prices(prices: Dict[str, Any]) -> None:
    with open('prices.json', 'w') as f:
        json.dump(prices, f)

def load_prices() -> Dict[str, Any]:
    try:
        with open('prices.json', 'r') as f:
            data: Dict[str, Any] = json.load(f)
            # Convert old format to new format during load
            for url in data:
                if 'prices' in data[url]:
                    prices = data[url]['prices']
                    # Check if prices are in old format (just strings)
                    if prices and isinstance(prices[0], str):
                        # Convert to new format with today's date
                        data[url]['prices'] = [(price, "2023-12-04") for price in prices]
            return data
    except FileNotFoundError:
        return {}

def load_products() -> List[str]:
    with open('products.txt') as f:
        products = f.readlines()
    return products

def get_status_color(status: str) -> str:
    if OUT_OF_STOCK.lower() in status.lower():
        return Style.BRIGHT + Fore.WHITE + Back.RED + status
    elif IN_STOCK.lower() not in status.lower():
        return Style.BRIGHT + Fore.WHITE + Back.YELLOW + status
    else:
        return Style.BRIGHT + Fore.WHITE + Back.GREEN + status

def get_warning_color(warning_old: str, warning_now: Optional[str] = None) -> Any:
    if warning_now and warning_old != warning_now:
        return (Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning_old if warning_old else ""
            , Style.RESET_ALL, '--> ', Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning_now if warning_now else "")
    elif warning_now:
        return (Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning_now if warning_now else "")
    else:
        return ""

def sort_prices(prices: List[Any]) -> List[str]:
    # Extract just the price strings from tuples if in new format
    if prices and isinstance(prices[0], (list, tuple)):
        price_strings = [p[0] for p in prices]
    else:
        price_strings = prices
    
    prices_clean = [price_to_number(p) for p in price_strings]
    prices_sorted = [x for _, x in sorted(zip(prices_clean, price_strings))]
    return prices_sorted

def get_price_color(price_now: str, prices: List[Any]) -> str:
    # Extract just the price strings from tuples if in new format
    if prices and isinstance(prices[0], (list, tuple)):
        price_strings = [p[0] for p in prices]
        price_dates = [p[1] for p in prices]
    else:
        price_strings = prices
        price_dates = [None] * len(prices)
    
    # Sort prices and dates together to maintain correspondence (fixes bug with duplicate prices)
    sorted_pairs = sorted(zip(price_strings, price_dates), key=lambda x: int(x[0].replace('R','').replace(',','').strip()))
    prices_sorted, dates_sorted = zip(*sorted_pairs) if sorted_pairs else ([], [])
    
    prices_clean = [price_to_number(p) for p in prices_sorted]
    current_date = datetime.now().strftime('%Y-%m-%d')

    res = ""

    for i, price_ in enumerate(prices_sorted):
        price_clean = price_to_number(price_)

        # Get the date for this price from the sorted dates
        price_date = dates_sorted[i] if i < len(dates_sorted) else None

        # Color logic: Prioritize lowest today (CYAN), then current price (BLUE), then lowest (GREEN), highest (RED), else default
        if price_clean <= min(prices_clean) and price_date == current_date:
            price_color = Style.BRIGHT + Fore.WHITE + Back.CYAN
        elif price_ == price_now:
            price_color = Style.BRIGHT + Fore.WHITE + Back.BLUE
        elif price_clean <= min(prices_clean):
            price_color = Style.BRIGHT + Fore.WHITE + Back.GREEN
        elif price_clean >= max(prices_clean):
            price_color = Style.BRIGHT + Fore.WHITE + Back.RED
        else:
            price_color = Style.RESET_ALL + Style.NORMAL

        res += price_color + prices_sorted[i] + Style.RESET_ALL + ' '

    return res.strip()

def is_lowest_price(price_now: str, prices: List[Any]) -> bool:
    """
    Checks if the current price is the lowest among the given prices.

    Args:
        price_now: The current price to check.
        prices: A list of prices to compare against (can be strings or tuples).

    Returns:
        bool: True if the current price is the lowest, False otherwise.
    """
    if len(prices) < 2:
        return False

    # Extract just the price strings from tuples if in new format
    if prices and isinstance(prices[0], (list, tuple)):
        price_strings = [p[0] for p in prices]
    else:
        price_strings = prices
    
    prices_clean = [price_to_number(p) for p in price_strings]
    return price_to_number(price_now) <= min(prices_clean)

def retry(func: Callable[[], Any], url: str, retries: int = 3, *, delay: int = 1) -> Any:
    """
    Retries a function a specified number of times on TimeoutException.

    Args:
        func: The function to retry.
        retries: The number of retries allowed (default: 3).
        delay: The delay in seconds between retries (default: 1).

    Returns:
        The result of the successful function call.

    Raises:
        Exception: If the function fails after all retries.
    """
    for _ in range(retries):
        try:
            return func(url)
        except Exception as ex:
            print(ex)
            time.sleep(delay)
            print(f"Retrying function \"{func.__name__}\"...")
    last_exception = None
    for _ in range(retries):
        try:
            return func()
        except Exception as ex:
            last_exception = ex
            print(ex)
            time.sleep(delay)
            print(f"Retrying function \"{func.__name__}\"...")
    if last_exception:
        raise last_exception

# convert price "R 4,599" to number
def price_to_number(price: str) -> int:
    return int(price.replace('R','').replace(',','').strip())

def get_prices(products: List[str], prices_db: Dict[str, Any]) -> Dict[str, Any]:
    res: Dict[str, Any] = {}

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

            # Check if URL has a stored title with '404' and skip if so
            if url in prices_db and 'title' in prices_db[url] and '404' in prices_db[url]['title']:
                print(f"Skipping {url} due to previous 404 error.")
                continue

            # navigate to a page
#            url = "https://www.takealot.com/xiaomi-redmi-9t-128gb-carbon-grey/PLID72013248"
#            print(url, '-', end=' ')                 
            print(url)              

#            driver.get(url)

            try:
                # Retry driver.get() on TimeoutException
                retry(lambda url: driver.get(url), url, retries=3, delay=2)

                time.sleep(1) # enough time to load the base page
                
                title = driver.title
                print(title)
            except Exception as ex:
                print(ex)
                continue

            if '404' in title:
                res[url] = {'title':title}
            else:
                try:
                    # Wait until the 'div.sf-buybox' element is loaded
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sf-buybox [data-ref='price']")))
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sf-buybox [data-ref='in-stock-indicator']")))
                except Exception as ex:
                    print(ex)
                    continue

                # retrieve text

                # <span class="currency plus currency-module_currency_29IIm" data-ref="buybox-price-main">R 4,250</span>
#                element = driver.find_element(By.CSS_SELECTOR,'div.sf-buybox')
#                element = driver.find_element(By.CSS_SELECTOR, "div[class*='pdp-module_sidebar-buybox']")
                element = driver.find_element(By.CSS_SELECTOR, "div.sf-buybox [data-ref='price'] > span:first-child")

                # Extract the prices from the element's text
#                prices = [price for price in element.text.split('\n') if price.startswith('R')]

#                pprint(element)
#                print(dir(element))

                prices = [element.text]

#                pprint(prices)
                assert len(prices) > 0

                # <div class="cell shrink stock-availability-status" data-ref="stock-availability-status"><span>In stock</span></div>
                element = driver.find_element(By.CSS_SELECTOR,"div.sf-buybox [data-ref='in-stock-indicator']")
                status = element.text
                status = status.replace('\n',' ').strip()

                if 'get it tomorrow' in status.lower():
                    status = IN_STOCK

                # <span class="rounded-pill " data-ref="buybox-only-x-left">Only 20 left</span>
    #            warning = driver.find_element(By.CSS_SELECTOR,'span.rounded-pill')
                warnings = driver.find_elements(By.CSS_SELECTOR,'span.rounded-pill')
                if warnings:
                    warning = warnings[0].text
                else:
                    warning = ''
#                print('warning:', warning)

                print(get_price_color(prices[0], prices), '-', end=' ')

                status_color = get_status_color(status)
                
                print(status_color, '- ' + Style.BRIGHT + Fore.WHITE + Back.MAGENTA + warning if warning else "")                     
                
                res[url] = {'prices':prices, 'status':status,'warning':warning,'title':title}

#                pprint(res[url])
#                input('Press enter to continue...')

            print()
#            sys.exit(1)

        return res
    
    finally:
        # close the browser
        driver.quit()


def main() -> bool:

#    prices = ['R 11,499','R 12,999','R 9,499']
#    pprint(sort_prices(prices))
#    return

    colorama.init(autoreset=True)

    products = load_products()
    
    # Load PRICES_DB once here
    PRICES_DB = load_prices()

    prices_now = get_prices(products, PRICES_DB)

    print('-'*37,'alerts','-'*37)

    PRICE_DROPS: List[str] = []

    got_alert = False
    for url in prices_now.keys():

        # price now is always the first price in the list
        prices_ = prices_now[url].get('prices', [])
        price_now = prices_[0] if prices_ else None
        
        status_now = prices_now[url].get('status', None)
        warning_now = prices_now[url].get('warning', None)
        title_now = prices_now[url].get('title', None)

        new_item = False
        if url not in PRICES_DB: # new item

            price_old = price_now

            data = {'prices':[], 'price_now':price_now, 'status':status_now, 'warning':warning_now, 'title':title_now}
            data = {k: v for k, v in data.items() if v is not None}

            PRICES_DB[url] = data
            
            new_item = True
        else: # existing item

            price_old = PRICES_DB[url].get('price_now', '')

            status_old = PRICES_DB[url].get('status', '')
            warning_old = PRICES_DB[url].get('warning', '')

            back_in_stock = OUT_OF_STOCK.lower() in status_old.lower() and status_old != status_now

            data = {'price_now':price_now, 'status':status_now, 'warning':warning_now, 'title':title_now}
            data = {k: v for k, v in data.items() if v is not None}

            PRICES_DB[url].update(data)

        # Check for new prices and add them with current date
        stored_prices = PRICES_DB[url]['prices']
        
        # Extract price strings from stored prices for comparison
        if stored_prices and isinstance(stored_prices[0], (list, tuple)):
            stored_price_strings = [p[0] for p in stored_prices]
        else:
            stored_price_strings = stored_prices

        current_date = datetime.now().strftime('%Y-%m-%d')

        new_prices = [price for price in prices_now[url].get('prices', []) if price not in stored_price_strings]
        for new_price in new_prices:
            PRICES_DB[url]['prices'].append((new_price, current_date))

        # # Update date for current price_now if it exists in prices list
        # if price_now and stored_prices:
        #     for i, price_entry in enumerate(stored_prices):
        #         if isinstance(price_entry, (list, tuple)) and price_entry[0] == price_now:
        #             PRICES_DB[url]['prices'][i] = (price_now, current_date)
        #             break
        #         elif isinstance(price_entry, str) and price_entry == price_now:
        #             PRICES_DB[url]['prices'][i] = (price_now, current_date)

        if not new_item:
            if price_now != price_old or new_prices or status_old != status_now or warning_old != warning_now or back_in_stock:

                print(url)
                print(title_now)

                if price_now is not None:
                    print(get_price_color(price_now, PRICES_DB[url]['prices']))

                    if price_now != price_old:
                        print(price_old, '--> ', get_price_color(price_now, [price_now]))

                if status_now is not None:
                    if status_old != status_now:
                        print(get_status_color(status_old), Style.RESET_ALL, '--> ', get_status_color(status_now))
                    else:
                        print(get_status_color(status_now))

                if warning_now:
                    print(get_warning_color(warning_old, warning_now))

                print()

                if price_now is not None:
                    if (
                        (price_to_number(price_now) < price_to_number(price_old))
                        or (
                            OUT_OF_STOCK.lower() not in status_now.lower()
                            and is_lowest_price(price_now, PRICES_DB[url]['prices'])
                        )
                    ):
                        PRICE_DROPS.append(url)

                got_alert = True

    print('#'*170)
    print('#'*70,'price drop and back in stock','#'*70)
    print('#'*170)

    for url in PRICE_DROPS:
        if 'supplier out of stock' not in PRICES_DB[url]['status'].lower():
            print(url)
            print(PRICES_DB[url]['title'])
            print(get_price_color(PRICES_DB[url]['price_now'], PRICES_DB[url]['prices']))
            print(get_status_color(PRICES_DB[url]['status']))
            print(get_warning_color(PRICES_DB[url]['warning']))
            print()

    # save prices to file
    save_prices(PRICES_DB)

    return got_alert


if __name__ == '__main__':
    try:
        res=main()
        if res:
            input('Press enter to exit...')
    except Exception:
        traceback.print_exc()  # This will print the full stack trace
        input('Press enter to exit...')
