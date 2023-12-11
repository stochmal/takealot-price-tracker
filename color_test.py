import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

foreground_colors = [Fore.BLACK, Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
background_colors = [Back.BLACK, Back.RED, Back.GREEN, Back.YELLOW, Back.BLUE, Back.MAGENTA, Back.CYAN, Back.WHITE]

color_names = ['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE']

for j, bg in enumerate(background_colors):
    for i, fg in enumerate(foreground_colors):
        print(f"{fg}{bg}Foreground color: {color_names[i]} Background color: {color_names[j]}")

print(Style.RESET_ALL)

