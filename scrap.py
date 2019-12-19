from selenium import webdriver

from pymongo import MongoClient
import re

home = 'https://stats.nba.com/players/list/?Historic=Y'

browser = webdriver.Chrome(executable_path="./chromedriver")

browser.get(home)

# Player structure example to insert in mongodb
# player = {
#     'id': '76001'
#     'name': 'Alaa Abdelnaby',
#     'position': 'F',
#     'Carrer Regular Season Stats': [
#         {
#             'SEASON': '1994-95',
#             'TEAM': 'SAC',
#             'AGE': '27',
#             ...
#         }
#     ],
#     'Carrer Playoffs Stats': [],
#     'Carrer League Ranking Stats': []
# }

# Connects and create db and collections
conn = MongoClient('localhost', 27017)
db = conn.nbascrapper
players_collection = db.players

print('Searching players IDs...')
# Gets every player id on the page
player_documents = []
players_list = browser.find_elements_by_xpath("//li[@class='players-list__name']//a")
for player_item in players_list:
    links_list.append(player_item.get_attribute('href').replace('/player/'))

print('Searching players data...')
# Iterate over the players ID list to access his respective page and get all info
try:
    for link in links_list:
        player = {}
        # Access his page
        browser.get(link)
        # Get player name and format it for the folder name
        name = browser.find_elements_by_xpath('//div[@class="player-summary__player-name"]')
        player['name'] = ' '.join(name[0].text.split('\n'))
        # Find the table where all the statistics tables are
        stats_tables = browser.find_elements_by_xpath('//nba-stat-table')
        # Iterate over each table and create your own csv file
        table = []
        for index_table, stats_table in enumerate(stats_tables):
            table = []
            # Get the table name
            caption_item = stats_table.find_elements_by_xpath('.//div[@class="nba-stat-table__caption"]')
            caption = 'Table'+str(index_table) if len(caption_item) == 0 else caption_item[0].text
            player[caption] = []
            # Get the columns names
            head = []
            col_list = stats_table.find_elements_by_xpath('.//div[@class="nba-stat-table__overflow"]/table/thead/tr/th')
            # Get the values of each row
            row_list = stats_table.find_elements_by_xpath('.//div[@class="nba-stat-table__overflow"]/table/tbody/tr')
            for index_row, row in enumerate(row_list):
                body = {}
                body_col_list = row.find_elements_by_xpath('.//td')
                for index_col, row_col in enumerate(body_col_list):
                    body[col_list[index_col].text] = row_col.text
                table.append(body)
        
        player_documents.append(table)
except:
    print(player_documents)
    #players_collection.insert_many(player_documents)

#players_collection.insert_many(player_documents)

# Closes the browser
print('Data colected, closing driver...')
browser.close()