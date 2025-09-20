import unittest
from unittest.mock import patch
from datetime import datetime
from colorama import Style, Fore, Back

# Import the function to test
from tracker import get_price_color, is_lowest_price, sort_prices

class TestGetPriceColor(unittest.TestCase):
    def setUp(self):
        # Mock today's date for consistent testing
        self.mock_date = '2023-12-04'
        self.patcher = patch('tracker.datetime')
        mock_datetime = self.patcher.start()
        mock_datetime.now.return_value = datetime.strptime(self.mock_date, '%Y-%m-%d')

    def tearDown(self):
        self.patcher.stop()

    def test_old_format_lowest_price(self):
        price_now = 'R 100'
        prices = ['R 100', 'R 200', 'R 300']
        result = get_price_color(price_now, prices)
        # Current price (lowest) should be blue, others normal except highest red
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.BLUE + 'R 100', result)
        self.assertIn(Style.RESET_ALL + Style.NORMAL + 'R 200', result)
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.RED + 'R 300', result)

    def test_new_format_current_lowest_today(self):
        price_now = 'R 100'
        prices = [('R 100', self.mock_date), ('R 200', '2023-12-03')]
        result = get_price_color(price_now, prices)
        # Lowest today should be cyan, highest should be red
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.CYAN + 'R 100', result)
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.RED + 'R 200', result)

    def test_new_format_highest_price(self):
        price_now = 'R 300'
        prices = [('R 100', '2023-12-03'), ('R 200', '2023-12-03'), ('R 300', '2023-12-03')]
        result = get_price_color(price_now, prices)
        # Current (highest) should be blue, lowest green, middle normal
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.BLUE + 'R 300', result)
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.GREEN + 'R 100', result)
        self.assertIn(Style.RESET_ALL + Style.NORMAL + 'R 200', result)

    def test_mixed_prices(self):
        price_now = 'R 150'
        prices = ['R 100', 'R 150', 'R 200']
        result = get_price_color(price_now, prices)
        # Current should be blue, lowest green, highest red
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.BLUE + 'R 150', result)
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.GREEN + 'R 100', result)
        self.assertIn(Style.BRIGHT + Fore.WHITE + Back.RED + 'R 200', result)

    def test_empty_prices(self):
        price_now = 'R 100'
        prices = []
        result = get_price_color(price_now, prices)
        self.assertEqual(result, '')

class TestIsLowestPrice(unittest.TestCase):
    def setUp(self):
        # Mock today's date for consistent testing
        self.mock_date = '2023-12-04'
        self.patcher = patch('tracker.datetime')
        mock_datetime = self.patcher.start()
        mock_datetime.now.return_value = datetime.strptime(self.mock_date, '%Y-%m-%d')

    def tearDown(self):
        self.patcher.stop()

    def test_old_format_is_lowest(self):
        price_now = 'R 100'
        prices = ['R 100', 'R 200', 'R 300']
        result = is_lowest_price(price_now, prices)
        self.assertTrue(result)

    def test_old_format_not_lowest(self):
        price_now = 'R 200'
        prices = ['R 100', 'R 200', 'R 300']
        result = is_lowest_price(price_now, prices)
        self.assertFalse(result)

    def test_new_format_is_lowest_today(self):
        price_now = 'R 100'
        prices = [('R 100', self.mock_date), ('R 200', '2023-12-03')]
        result = is_lowest_price(price_now, prices)
        self.assertTrue(result)

    def test_new_format_not_lowest(self):
        price_now = 'R 200'
        prices = [('R 100', '2023-12-03'), ('R 200', self.mock_date)]
        result = is_lowest_price(price_now, prices)
        self.assertFalse(result)

    def test_empty_prices(self):
        price_now = 'R 100'
        prices = []
        result = is_lowest_price(price_now, prices)
        self.assertFalse(result)  # Assuming it returns False for empty list

class TestSortPrices(unittest.TestCase):
    def test_old_format_sort(self):
        prices = ['R 300', 'R 100', 'R 200']
        result = sort_prices(prices)
        self.assertEqual(result, ['R 100', 'R 200', 'R 300'])

    def test_new_format_sort_by_date_desc(self):
        prices = [('R 100', '2023-12-01'), ('R 200', '2023-12-03'), ('R 150', '2023-12-02')]
        result = sort_prices(prices)
        self.assertEqual(result, ['R 100', 'R 150', 'R 200'])

    def test_empty_list(self):
        prices = []
        result = sort_prices(prices)
        self.assertEqual(result, [])

    def test_single_price(self):
        prices = ['R 100']
        result = sort_prices(prices)
        self.assertEqual(result, ['R 100'])

if __name__ == '__main__':
    unittest.main()
