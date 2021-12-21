import os
import telebot
from telebot import types
import psycopg2
import random
from dotenv import load_dotenv

#Initialise sensitive info (Store either in .env file or config file)
load_dotenv()

API_KEY = os.environ['API_KEY']
DATABASE_URL = os.environ['DATABASE_URL']

#Connect to postgresql (heroku for production, local for development)
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

bot = telebot.TeleBot(API_KEY)

# List of mrt stations that bot is able to query
mrt = ['admiralty', 'aljunied', 'ang-mo-kio', 'balestier', 'bartley', 'bayfront', 'beach-road', 'beauty-world', 'bedok', 'bedok-north', 'bedok-reservior', 'bencoolen', 'bendemeer', 'bishan', 'boat-quay', 'boon-keng', 'boon-lay', 'botanic-gardens', 'braddell', 'bras-basah', 'buangkok', 'bugis', 'bukit-batok', 'bukit-gombak', 'bukit-merah', 'bukit-panjang', 'bukit-timah', 'buona-vista', 'caldecott', 'canberra', 'cantonment', 'cashew', 'changi', 'changi-airport', 'chinatown', 'chinese-garden', 'choa-chu-kang', 'city-hall', 'clarke-quay', 'clementi', 'club-street', 'commonwealth', 'dakota', 'dempsey', 'dhoby Ghaut', 'dhoby-ghaut', 'dover', 'downtown', 'duxton', 'east-coast', 'esplanade', 'eunos', 'expo', 'farrer-park', 'farrer-road', 'fort-canning', 'geylang', 'geylang-bahru', 'great-world', 'harbourfront', 'haw-par-villa', 'hillview', 'holland-village', 'hougang', 'jalan-besar', 'joo-chiat', 'joo-koon', 'jurong', 'jurong-east', 'kaki-bukit', 'kallang', 'kampong-bahru', 'katong', 'kembangan', 'kent-ridge', 'keong-saik', 'keppel', 'khatib', 'king-albert-park', 'kovan', 'kranji', 'labrador-park', 'lakeside', 'lavender', 'little-india', 'lorong-chuan', 'macpherson', 'marina-bay', 'marina-south-pier', 'marine-parade', 'marsiling', 'marymount', 'mattar', 'mountbatten', 'neil-road', 'newton', 'nicoll-highway', 'novena', 'one-north', 'orchard', 'orchard-road', 'outram', 'outram-park', 'pasir-panjang', 'pasir-ris', 'paya-labar', 'paya-lebar', 'pioneer', 'potong-paisr', 'potong-pasir', 'prince-edward', 'promenade', 'punggol', 'queenstown', 'raffles-place', 'redhill', 'river-valley', 'robertson-quay', 'rochester', 'rochor', 'seletar', 'sembawang', 'sengkang', 'sentosa', 'serangoon', 'siglap', 'simei', 'sixth-avenue', 'somerset', 'stadium', 'stevens', 'suntec', 'tai-seng', 'tampines', 'tanah-merah', 'tanglin', 'tanjong-pagar', 'telok-ayer', 'telok-blangah', 'thomson', 'tiong-bahru', 'toa-payoh', 'tuas', 'ubi', 'upper-changi', 'west-coast', 'woodlands', 'woodleigh', 'yew-tee', 'yio-chu-kang', 'yishun']

#Create 2 different markup keyboards which forces user to reply in exact format
markup_mrt = types.ReplyKeyboardMarkup(row_width=5)
for m in mrt:
    markup_mrt.add(types.KeyboardButton(m))

prices = ["Affordable", "Mid-Range", "High-End", "No preference"]

markup_prices = types.ReplyKeyboardMarkup(row_width=5)
for p in prices:
    markup_prices.add(types.KeyboardButton(p))


user_request_loc = {}

@bot.message_handler(commands=['start', 'Start'])
def start(message):
    bot.reply_to(message, "Where would you like to eat?", reply_markup=markup_mrt)

def check_valid_station(message):
    return message.text in mrt

@bot.message_handler(func = check_valid_station)
def give_price_options(message):
    user_request_loc[message.from_user.id] = message.text
    bot.reply_to(message, "What is your budget? Selecting no preference will give you a wider range of results.", reply_markup=markup_prices)

def check_valid_input(message):
    return (message.from_user.id in user_request_loc) and message.text in prices

@bot.message_handler(func = check_valid_input)
def give_food_options(message):
    try:
        emoji_dict = {1: '📌', 2: '🏠', 3: '📞', 4: '⏰', 5: '💻'}
        
        #user wants a specific price
        if message.text != "No preference":
            cursor.execute('''SELECT * FROM SETH WHERE location = %s AND price = %s ORDER BY RANDOM() LIMIT 1''', (user_request_loc[message.from_user.id] ,message.text))
            result = cursor.fetchone()
        
        #user has no preference on what price range -> able to query from both DB as MTC does not have price information available
        else:
            result = None
            while (result == None):
                
                #arbitary flag to randomly choose database -> can expand to RNG if more DB is added
                db_decider = bool(random.getrandbits(1))

                if db_decider:
                    cursor.execute('''SELECT * FROM MTC WHERE location = %s ORDER BY RANDOM() LIMIT 1''', (user_request_loc[message.from_user.id],))
                    result = cursor.fetchone()
                else: 
                    cursor.execute('''SELECT * FROM SETH WHERE location = %s ORDER BY RANDOM() LIMIT 1''', (user_request_loc[message.from_user.id],))
                    result = cursor.fetchone()

        #Format message nicely for user to see if a suitable food option has been found
        s = ''
        for i in range(1,6):
            if (result[i] is not None) and (result[i] != ''):
                s += emoji_dict.get(i) + ': ' + result[i]
                s += '\n'
        s += "To find another place to eat, you can click the same location again!"
        bot.reply_to(message, s)
        bot.reply_to(message, "Where would you like to eat?", reply_markup=markup_mrt)
    except:
        bot.reply_to(message, "No food locations at price point. Select no preference instead!")




bot.infinity_polling()
