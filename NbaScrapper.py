from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from re import sub
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep
from random import uniform


class NbaScrapper():
    """
    Scrapper for NBA stats: players, teams, seasons, infos etc and saves to mongodb.
    """

    url_stats = 'https://stats.nba.com/'

    def __init__(self, path_driver="./chromedriver", url='localhost', port=27017):
        # Initializes selenium webdriver
        try:
            self.browser = webdriver.Chrome(executable_path=path_driver)
        except SessionNotCreatedException as e:
            print(f"Error creating session with selenium verify your ChromeDriver file! \n{e}")

        # Connects to mongodb and set collections necessary
        conn = self.mongodb_conn(url, port)
        if conn is None:
            print("No mongodb connections found!")
            self.browser.close()
            return

        db = conn.nbascrapper

        self.collection_players = db.players
        self.collection_glossary = db.glossary
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.browser.close()
    
    def mongodb_conn(self, url, port):
        try:
            return MongoClient(url, port)
        except ConnectionFailure as e:
            print(f"Could not connect to server: {e}")

    def search_players_ids(self, historic=True):
        # Builds a list with player's IDs
        print('Searching players IDs...')
        self.browser.get(f'{self.url_stats}players/list/?Historic={"Y" if historic else "N"}')
        players = self.browser.find_elements_by_xpath("//li[@class='players-list__name']//a")

        players_list = []
        for player in players:
            id = sub(r"[^0-9]", "", player.get_attribute('href'))
            if self.collection_players.find({'id': id}).limit(1).count() == 0:
                players_list.append({'id': sub(r"[^0-9]", "", player.get_attribute('href')), 'stats': {}})

        return players_list
    
    def search_players_data(self, historic=True):
        """ 
        Iterate over the players ID list to access his respective page and get all info

        Player structure example to insert in mongodb
        player = {
            'id': '76001',
            'name': 'Alaa Abdelnaby',
            'position': 'F'
            'stats': {
                    'Carrer Regular Season Stats': [
                    {
                        'SEASON': '1994-95',
                        'TEAM': 'SAC',
                        'AGE': '27',
                        ...
                    }
                ],
                'Carrer Playoffs Stats': [],
                'Carrer League Ranking Stats': []
            }
        }
        """

        players = self.search_players_ids(historic)

        if players is None or len(players) == 0:
            print("Players IDs not found! Verify URL and xpath.")
            return

        print('Searching player(s) data...')
        for player in players:
            if self.collection_players.find(player).limit(1).count() == 0:
                # Access player's page
                self.browser.get(f'{self.url_stats}player/{player["id"]}')
                # Get player's name and position
                name = self.browser.find_elements_by_xpath('//div[@class="player-summary__player-name"]')
                player['name'] = name[0].text.replace('\n', ' ')

                position = self.browser.find_elements_by_xpath('//span[@ng-if="playerInfo.POSITION_INITIALS"]')
                player['position'] = position[0].text if len(position) > 0 else ''

                # Find the table element on the page where all the statistics tables are
                # Checking if tables have already loaded
                for i in range(0, 10):
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                    tables = soup.findAll('nba-stat-table')
                    
                    if len(tables) > 0:
                        break

                    sleep(1)
                
                if len(tables) == 0:
                    print(f'Stats for player #{player["id"]} ({player["name"]}) not loaded!')
                    continue
                
                # get tables names
                caption_item = self.browser.find_elements_by_xpath('.//div[@class="nba-stat-table__caption"]')

                # Convert tables to dataframe and then from dataframe to json to save on mongodb
                json_stats = None
                df = None
                for index, table in enumerate(tables):
                    try:
                        df = pd.read_html(table.prettify())
                    except ValueError as e:
                        print(f'Error parsing player #{player["id"]}: {e} \n\n{table.prettify()}')

                    if df:
                        json_stats = df[0].to_dict(orient='records')

                    player['stats'][caption_item[index].text] = json_stats

                self.collection_players.insert(player)
        
            # Random time to go to next page, trying to avoid robot detection
            sleep(uniform(0.5, 2.5))
    
    def search_glossary(self):
        """
        Search for all NBA acronyms from NBA stats glossary
        """
        print('Searching glossary...')
        self.browser.get(f'{self.url_stats}help/glossary/')

        soup = BeautifulSoup(self.browser.page_source, 'lxml')

        # Get all stats from list to iterate over
        items = soup.findAll("article", {"class": "stats-glossary-page__item"})

        stat = {}
        for item in items:
            # Get stat name
            key = item.find("h2", {"class": "stats-glossary-page__title"}).find("abbr").text
            stat = {
                "Key": key
            }
            
            # Get stat properties
            properties_names = item.find("dl", {"class": "stats-glossary-page__properties"}).findAll("dt", {"class":"stats-glossary-page__prop"})
            properties_values = item.find("dl", {"class": "stats-glossary-page__properties"}).findAll("dd", {"class":"stats-glossary-page__value"})

            for index, value in enumerate(properties_values):
                try:
                    name = properties_names[index].text
                    if name == "Contexts":
                        stat[name] = value.text.strip().split('\n')
                    else:
                        stat[name] = value.text
                except KeyError:
                    print("Key or property not found in glossary stats list!")
                    print(key)
                    print(index)
                    print(value.text)

            self.collection_glossary.insert(stat)