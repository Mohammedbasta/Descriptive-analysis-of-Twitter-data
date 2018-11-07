

#######################################################################################
import sqlite3
conn = sqlite3.connect('db_final.db')
cursor = conn.cursor()

# creation de la table tweet
cursor.execute("""
CREATE TABLE IF NOT EXISTS tweet(
     id INTEGER PRIMARY KEY,
     id_tweet TEXT,
     txt TEXT,
     create_at DATETIME,
     user_id TEXT,
     user_name TEXT,
     user_country TEXT,
     user_country_code TEXT,
     user_lat TEXT,
     user_long TEXT,
     user_region TEXT,
     user_gender TEXT,
     lang TEXT,
     retweet_count INTERGER,
     like_count INTERGER,
     sentiment TEXT
)
""")
conn.commit()

#######################################################################################

import json
import urllib
import requests
import nltk
import sqlite3
import pandas as pd
import time


# nettoyage de la tweet
def clean_tweet(text):
    text = nltk.re.sub(r"http\S+", "", text)
    text = " ".join((nltk.re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|([RTrt])", " ", text)).split())
    return nltk.re.sub(r'\d+', '', text)


# creaion des urls constants
url_sentiment = 'http://api.datumbox.com/1.0/SentimentAnalysis.json?api_key=6451de5d31d3a89b89e9546000463a88&text='
url_gender = 'http://api.datumbox.com/1.0/GenderDetection.json?api_key=0a340379056516fd560aece59dabbd0b&text='
url_loc = 'http://api.geonames.org/searchJSON?username=youneszorro&q='

# connexion a la base
conn = sqlite3.connect('db_final.db')
cursor = conn.cursor()

# lecture du fishier
with open('humanrightsday.json', 'r') as f:
    i = 1
    for line in f:
        country = None
        country_code = None
        lat = None
        long = None
        region = None
        sentiment = None
        gender = None

        #         la condition est utiliser pour relancer la transformation
        if (i > 41535):
            tweet = json.loads(line)
            username = tweet["user"]["name"]
            text_tweet = clean_tweet(tweet["text"])
            place = tweet["place"]
            location = tweet["user"]["location"]

            # si le tweet possède l'attribut place en l'ajoute directement
            if (place is not None):
                country = tweet["place"]["country"]
                country_code = tweet["place"]["country_code"]
                lat = tweet['place']['bounding_box']["coordinates"][0][0][0]
                long = tweet['place']['bounding_box']["coordinates"][0][0][1]

            elif (location is not None):
                param_loc = urllib.parse.quote((u'' + str(location)).encode('utf8'))

                # appele API pour avoir le pays apartir de la atribut location de l'user'
                result_loc = requests.get(url_loc + param_loc).json()
                if (result_loc['totalResultsCount'] > 0):
                    try:
                        country = result_loc['geonames'][0]['countryName']
                        country_code = result_loc['geonames'][0]['countryCode']
                        lat = result_loc['geonames'][0]['lat']
                        long = result_loc['geonames'][0]['lng']
                    except:
                        pass
                else:
                    # si en obtien de resultats en split l'attr location en part
                    split_loc = location.split()
                    count_result = []
                    result = []

                    # appel de l'API pour chaque part
                    for t in split_loc:
                        if len(t) > 4:
                            param_loc1 = urllib.parse.quote((u'' + str(t)).encode('utf8'))
                            result_loc1 = requests.get(url_loc + param_loc1).json()
                            if (result_loc1['totalResultsCount'] > 0):
                                try:
                                    count_result.append(result_loc1['totalResultsCount'])
                                    inter_country = result_loc1['geonames'][0]['countryName']
                                    inter_country_code = result_loc1['geonames'][0]['countryCode']
                                    inter_lat = result_loc1['geonames'][0]['lat']
                                    inter_long = result_loc1['geonames'][0]['lng']
                                    result.append({'count': result_loc1['totalResultsCount'], 'country': inter_country,
                                                   'country_code': inter_country_code, 'lat': inter_lat,
                                                   'long': inter_long})
                                except:
                                    pass

                    for t in result:
                        # ajouter le plus present
                        if (t['count'] == max(count_result)):
                            country = t['country']
                            country_code = t['country_code']
                            lat = t['lat']
                            long = t['long']

            if (country_code is not None):
                param_code = urllib.parse.quote((u'' + str(country_code)).encode('utf8'))
                url_code = 'http://api.worldbank.org/v2/countries/' + param_code + '?format=json'
                # appel de l'API pour recuperer la region du pays extrait en haut
                result_code = requests.get(url_code).json()
                try:
                    region = ((result_code[1][0])["region"])["value"]
                except:
                    print("          3 region ========>", i, result_code)
                    pass

            # recuperation du nom complet de la langue a partir de son code
            # en a utiliser ici un ficher plat
            df = pd.read_csv("lang.csv")
            df.set_index('code', inplace=True)
            langue = df.get_value(tweet["lang"], 'name') if tweet["lang"] in df.index else tweet["lang"]

            # formater la date
            date_tweet = time.strftime('%Y-%m-%d %H:%M:%S',
                                       time.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))

            # appel API pour avoir l'opinion de la tweet ( positive , negative ,neutre )
            result_sentiement = requests.get(
                url_sentiment + urllib.parse.quote((u'' + str(text_tweet)).encode('utf8'))).json()

            # appel API pour avoir le sexe de l'utilisateur

            result_gender = requests.get(url_gender + urllib.parse.quote((u'' + str(username)).encode('utf8'))).json()

            try:
                sentiment = result_sentiement['output']['result']
                gender = result_gender['output']['result']
            except:
                print("          4 sentiement ========>", i, result_sentiement)
                print("          5 gender ========>", i, result_gender)
                break

            data = {"id": i,
                    "id_tweet": tweet["id_str"],
                    "txt": tweet["text"],
                    "create_at": date_tweet,
                    "user_id": tweet["user"]["id_str"],
                    "user_name": tweet["user"]["name"],
                    "user_country": country,
                    "user_country_code": country_code,
                    "user_lat": lat,
                    "user_long": long,
                    "user_region": region,
                    "user_gender": gender,
                    "lang": langue,
                    "retweet_count": tweet["retweet_count"],
                    "like_count": tweet["favorite_count"],
                    "sentiment": sentiment
                    }

            # insertion de la tweet dans la base
            cursor.execute("""INSERT INTO tweet(id,id_tweet,txt,create_at,user_id,user_name,user_country,user_country_code,user_lat,user_long,user_region,user_gender,lang,retweet_count,like_count,sentiment)
                                          VALUES(:id,:id_tweet,:txt,:create_at,:user_id,:user_name,:user_country,:user_country_code,:user_lat,:user_long,:user_region,:user_gender,:lang,:retweet_count,:like_count,:sentiment)""",
                           data)

            conn.commit()

            print(i, username, country, country_code, lat, long, region, gender, sentiment, langue, date_tweet)
        i += 1
conn.close()
