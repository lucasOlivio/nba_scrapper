from selenium import webdriver

from pymongo import MongoClient
import sys, os
import time
import re

import pandas as pd
from bs4 import BeautifulSoup

home = 'https://stats.nba.com/players/list/?Historic=Y'

browser = webdriver.Chrome(executable_path="./chromedriver")

browser.get(home)

# Connects and create db and collections
conn = MongoClient('localhost', 27017)
db = conn.nbascrapper
players_collection = db.players

print('Searching players IDs...')
# Gets every player id on the page
players_list = browser.find_elements_by_xpath("//li[@class='players-list__name']//a")
links_list = []
for player_item in players_list:
	links_list.append(player_item.get_attribute('href'))

print('Searching players data...')
# Iterate over the players ID list to access his respective page and get all info
player = {}

# Player structure example to insert in mongodb
# player = {
# 	'id': '76001',
# 	'name': 'Alaa Abdelnaby',
# 	'position': 'F'
# 	'stats': {
# 			'Carrer Regular Season Stats': [
# 			{
# 				'SEASON': '1994-95',
# 				'TEAM': 'SAC',
# 				'AGE': '27',
# 				...
# 			}
# 		],
# 		'Carrer Playoffs Stats': [],
# 		'Carrer League Ranking Stats': []
# 	}
# }

try:
	for link in links_list:
		player_id = re.sub(r"[a-zA-Z\W]", "", link)

		if players_collection.find({'id': player_id}).limit(1).count() == 0:
			player = {
				'id': player_id,
				'stats': {}
			}
			# Access his page
			browser.get(f'{link}?SeasonType=Regular%20Season')
			# Get player name and format it for the folder name
			name = browser.find_elements_by_xpath('//div[@class="player-summary__player-name"]')
			position = browser.find_elements_by_xpath('//span[@ng-if="playerInfo.POSITION_INITIALS"]')
			player['name'] = ' '.join(name[0].text.split('\n'))
			player['position'] = position[0].text if len(position) > 0 else ''

			# Find the table where all the statistics tables are
			soup = BeautifulSoup(browser.page_source, 'lxml')
			tables = soup.findAll('nba-stat-table')

			# Check if tables are already loaded
			tries = 0
			while len(tables) == 0:
				tries += 1
				print('not loaded yet')
				time.sleep(1)
				soup = BeautifulSoup(browser.page_source, 'lxml')
				tables = soup.findAll('nba-stat-table')

				if tries == 5:
					break
			
			# get tables names
			caption_item = browser.find_elements_by_xpath('.//div[@class="nba-stat-table__caption"]')

			# Convert tables to dataframe and then from dataframe to json to save on mongodb
			json_stats = {}
			df = None
			for index, table in enumerate(tables):
				try:
					df = pd.read_html(table.prettify())
				except ValueError:
					print(f'{player_id}: {table.prettify()}')

				if df:
					json_stats = df[0].to_dict(orient='records')

				player['stats'][caption_item[index].text] = json_stats

			players_collection.insert(player)
except Exception as e:
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	print(exc_type, fname, exc_tb.tb_lineno)
	print(str(e))
	print(player)

# Closes the browser
print(len(links_list))
print('Data colected, closing driver...')
browser.close()