import os
from typing import Text
from bs4 import BeautifulSoup
import requests
import psycopg2
from dotenv import load_dotenv

#Initialise sensitive info (stored in .env file)
load_dotenv()

DATABASE = os.getenv('DATABASE')
DB_USER = os.getenv('DB_USER')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

#Connect to postgresql (heroku for production, local for development)
conn = psycopg2.connect(
    database=DATABASE, user=DB_USER, password=PASSWORD, host=HOST, port= PORT
)
#Setting auto commit false
conn.autocommit = False

#Creating a cursor object using the cursor() method
cursor = conn.cursor()

cursor.execute('''DROP TABLE IF EXISTS SETH''')

cursor.execute('''CREATE TABLE SETH (
    TcID SERIAL PRIMARY KEY,
    Address TEXT,
    Name Text,
    Phone TEXT,
    OpeningHours TEXT,
    Website TEXT,
    Location TEXT,
    Price TEXT
)''')

base = "https://sethlui.com/singapore/food/"
html_text2 = requests.get("https://sethlui.com/singapore/food/").text
soup2 = BeautifulSoup(html_text2, 'html.parser')
restaurants = soup2.find_all('div', id = 'filterLocation')
destinations = []

#Query all destinations available from SETH website [available even before clicking drop-down menu]
children = restaurants[0].find_all("span" , recursive=False)
for child in children:
    l = child.text.lower().split()
    temp = ''
    for word in l:
        temp += word + '-'
    destinations.append(temp[:-1])


for m in destinations:
    
    #Go to every location available
    website_with_mrt = base + m
    html_text2 = requests.get(website_with_mrt).text
    soup2 = BeautifulSoup(html_text2, 'lxml')
    restaurants = soup2.find_all('div', class_ = 'article-card__title')
    
    #Go to every restaurant available at each location
    for ele in restaurants:
        try:
            location = m
            name=address=phone=openinghours=website = ''
            tags = ele.find_all('a')
            price = tags[0].text
            
            # Most restaurants have 4 attributes specifically aranged in order
            if len(tags) == 4:
                website = tags[3].get('href')
                html_text3 = requests.get((tags[3].get('href'))).text
                soup3 = BeautifulSoup(html_text3, 'lxml')
                soup3.find('div', class_ = "review-left")
                info_box = soup3.find('div', class_ = "review-left")
                name = info_box.h4.text
                address = info_box.p.text
                
                # To make this consistent with the other DB (MTC), we do not include "Operating Hours: abcd"
                # but only abcd in our DB
                if info_box.find('div', class_ = "review-meta onlyshow"):
                    if info_box.find('div', class_ = "review-meta onlyshow").text != '\n':
                        phone = info_box.find('div', class_ = "review-meta onlyshow").text.split(' ', 1)[1]
                cursor.execute('''INSERT INTO SETH (Address, Name, Phone, OpeningHours, Website, Location, Price) 
                VALUES (%s, %s, NULLIF(%s,''), NULLIF(%s, ''), 
                %s, %s, %s)''', (address, name, phone, openinghours, 
                website, location, price))
        except AttributeError:
            continue

conn.commit()




