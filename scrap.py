from selenium import webdriver
from time import sleep

link = 'https://stats.nba.com/players/list/?Historic=Y'

browser = webdriver.Chrome(executable_path="./chromedriver")
browser.get(link)

sleep(3)

print('Searching players...')

players_list = browser.find_elements_by_xpath("//li[@class='players-list__name']//a")

for player_item in players_list:
    player_item.click()

    player_data = browser.find_elements_by_xpath("//div[@class='player-summary__player-name']")

    print(player_data.text)