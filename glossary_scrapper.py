from selenium import webdriver

from bs4 import BeautifulSoup
import requests

from pymongo import MongoClient


# Connects and create db and collections
conn = MongoClient('localhost', 27017)
db = conn.nbascrapper
glossary_collection = db.glossary

link = "https://stats.nba.com/help/glossary/"
browser = webdriver.Chrome(executable_path="./chromedriver")
browser.get(f'{link}?SeasonType=Regular%20Season')

soup = BeautifulSoup(browser.page_source, 'lxml')

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
            stat[properties_names[index].text] = value.text.replace('\n', ' - ')
        except:
            print(key)
            print(index)
            print(value.text)

    glossary_collection.insert(stat)

browser.close()