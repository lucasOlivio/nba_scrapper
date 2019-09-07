from selenium import webdriver
import sys, os, csv
sys.path.insert(0, './db_conf')

from postgres import PostDB

home = 'https://stats.nba.com/players/list/?Historic=Y'

browser = webdriver.Chrome(executable_path="./chromedriver")

browser.get(home)

db = PostDB()

# Test with DB
# if not db.checkDB():
#     if db.createDB():
#         if not db.importSQL('./db_conf/players_table.sql'):
#             db.dropDB()

print('Searching players IDs...')
# Gets every player id on the page
links_list = []
players_list = browser.find_elements_by_xpath("//li[@class='players-list__name']//a")
for player_item in players_list:
    links_list.append(player_item.get_attribute('href'))



print('Searching players data...')
# Iterate over the players ID list to access his respective page and get all info
folder = sys.argv[1]+'/'
for link in links_list:
    # Access his page
    browser.get(link)
    # Get player name and format it for the folder name
    name = browser.find_elements_by_xpath('//div[@class="player-summary__player-name"]')
    formated_name = ' '.join(name[0].text.split('\n'))
    player_folder = folder+formated_name+'/'
    # Checks if the folder already exists before creation
    if not os.path.exists(player_folder):
        os.makedirs(player_folder)
    # Find the table where all the statistics tables are
    stats_tables = browser.find_elements_by_xpath('//nba-stat-table')
    # Iterate over each table and create your own csv file
    table = []
    for index_table, stats_table in enumerate(stats_tables):
        table = []
        caption = []
        # Get the table name
        caption_item = stats_table.find_elements_by_xpath('.//div[@class="nba-stat-table__caption"]')
        caption = 'Table'+str(index_table) if len(caption_item) == 0 else caption_item[0].text
        # Get the columns names
        head = []
        col_list = stats_table.find_elements_by_xpath('.//div[@class="nba-stat-table__overflow"]/table/thead/tr/th')
        for index, col in enumerate(col_list):
            head.append(col.text)
        table.append(head)
        # Get the values of each row
        row_list = stats_table.find_elements_by_xpath('.//div[@class="nba-stat-table__overflow"]/table/tbody/tr')
        for index_row, row in enumerate(row_list):
            body = []
            col_list = row.find_elements_by_xpath('.//td')
            for index_col, row_col in enumerate(col_list):
                body.append(row_col.text)
            table.append(body)
        # Create a new csv file and save all information there
        with open(player_folder+caption+'.csv', 'w') as f:
            wr = csv.writer(f, dialect='excel')
            wr.writerows(table)

# Closes the browser
print('Data colected, closing driver...')
browser.close()