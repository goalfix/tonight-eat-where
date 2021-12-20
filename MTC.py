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

cursor.execute('''DROP TABLE IF EXISTS MTC''')

cursor.execute('''CREATE TABLE MTC (
    TcID SERIAL PRIMARY KEY,
    Address TEXT,
    Name Text,
    Phone TEXT,
    OpeningHours TEXT,
    Website TEXT,
    Location TEXT
)''')

#MTC locations by mrt, have to get all stations possible (Attribute hidden before clicking)
mrt = ["admiralty", "aljunied", "ang-mo-kio", "bartley", "bayfront", "beauty-world", "bedok", "bedok-north", "bedok-reservior", "bencoolen", "bendemeer", "bishan", "boon-keng", "boon-lay", "botanic-gardens", "braddell",
"bras-basah", "buangkok", "bugis", "bukit-batok", "bukit-gombak", "bukit-panjang", "buona-vista", "caldecott", "canberra", "cantonment", "cashew", "changi-airport", "chinatown", "chinese-garden", 
"choa-chu-kang", "city-hall", "clarke-quay","clementi", "commonwealth", "dakota", "dhoby Ghaut", "dover", "downtown", "esplanade", "eunos", "expo", "farrer-park", "farrer-road", "fort-canning", 
"geylang-bahru", "harbourfront", "haw-par-villa", "hillview", "holland-village", "hougang", "jalan-besar", "joo-koon", "jurong-east", "kaki-bukit", "kallang", "kembangan", "kent-ridge", "keppel", "khatib", "king-albert-park",
"kovan", "kranji", "labrador-park", "lakeside", "lavender", "little-india", "lorong-chuan", "macpherson", "marina-bay", "marina-south-pier", "marsiling", "marymount", "mattar", "mountbatten", "newton", "nicoll-highway", "novena", 
"one-north", "orchard", "outram-park", "pasir-panjang", "pasir-ris", "paya-labar", "pioneer", "potong-paisr", "prince-edward", "promenade", "punggol", "queenstown", 
"raffles-place", "redhill", "rochor", "sembawang", "sengkang", "sentosa", "serangoon", "simei", "sixth-avenue", "somerset", "stadium", "stevens", "tai-seng", 
"tampines", "tanah-merah", "tanjong-pagar", "telok-ayer", "telok-blangah", "tiong-bahru", "toa-payoh", "ubi", "upper-changi", "woodlands", "woodleigh", "yew-tee", "yio-chu-kang", "yishun"]

# Misstamchiak
base = "https://www.misstamchiak.com/tag/"

#Query every location from MTC
for m in mrt:
    try:
        website_with_mrt = base + m
        html_text2 = requests.get(website_with_mrt).text
        soup2 = BeautifulSoup(html_text2, 'lxml')
        restaurants = soup2.find_all('h3', class_ = 'entry-title')
        
        #Query every restaurant at each location
        for ele in restaurants:
            location = m
            name=address=phone=openinghours=website = ''
            website = ele.a.get('href')
            html_text3 = requests.get((ele.a.get('href'))).text
            soup3 = BeautifulSoup(html_text3, 'lxml')

            #html structure different than that of SETH
            if soup3.find('span', class_ = "company-address"):
                address = soup3.find('span', class_ = "company-address").text 
            if soup3.find('span', class_ = "company-phone"):
                phone = soup3.find('span', class_ = "company-phone").text
            if soup3.find('span', class_ = "company-opening_hours"):
                openinghours = soup3.find('span', class_ = "company-opening_hours").text     
            name = ele.string.split("–")[0]
            cursor.execute('''INSERT INTO MTC (Address, Name, Phone, OpeningHours, Website, Location) 
            VALUES (%s, %s, NULLIF(%s,''), NULLIF(%s, ''), 
            %s, %s)''', (address, name, phone, openinghours, 
            website, location))
            
    except AttributeError:
        pass
    
    # Commit your changes in the database
conn.commit()
