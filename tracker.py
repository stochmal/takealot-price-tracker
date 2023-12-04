import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

# Set up options for the driver
options = Options()
options.headless = True

# Set the path to the geckodriver executable
gecko_path = r'S:\GitHub\takealot-price-tracker\geckodriver-v0.33.0-win64\geckodriver.exe'

# Initialize the driver
#driver = webdriver.Firefox(executable_path=gecko_path, options=options)
driver = webdriver.Firefox(options=options)
try:
    # navigate to a page
    url = "https://www.takealot.com/xiaomi-redmi-9t-128gb-carbon-grey/PLID72013248"
    driver.get(url)

    # retrieve text

#    print(driver)
#    print(dir(driver))

#    element_text = driver.find_element_by_tag_name('body').text

# <span class="currency plus currency-module_currency_29IIm" data-ref="buybox-price-main">R 4,250</span>

    element = driver.find_element(By.CSS_SELECTOR ,'span.currency.plus.currency-module_currency_29IIm')    

    price = element.text
    print(price)
    assert price.startswith('R')   

finally:
    time.sleep(5)

    # close the browser
    driver.quit()
