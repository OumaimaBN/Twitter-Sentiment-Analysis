# import necessary modules
from kafka import KafkaConsumer
from pymongo import MongoClient
import json

# connect to mongo1 and desired database
try:
    client = MongoClient("mongodb://mongodb:27017")
    db = client.twitter_amz_DB
    print("Connected successfully!!!")
except:
    print("Could not connect to MongoDB")

# connect kafka consumer to desired kafka topic
consumer = KafkaConsumer('twitterstream', bootstrap_servers=['kafka:9092'])

# parse desired fields of json twitter object
for msg in consumer:
    print(msg)
    record = json.loads(msg.value)
    text = record['text']
    senti_val = record['senti_val'][:4]
    creation_datetime = record['creation_datetime']
    username = record['username']
    location = record['location']
    user_description = record['userDescr']
    followers = record['followers']
    retweets = record['retweets']
    favorites = record['favorites']

    # create dictionary and ingest data into mongo1
    try:
        twitter_rec = {'text': text, 'senti_val': senti_val, 'creation_datetime': creation_datetime,
                       'username': username, 'location': location,
                       'user_description': user_description, 'followers': followers, 'retweets': retweets,
                       'favorites': favorites}

        print(twitter_rec)
        rec_id1 = db.tweet_info.insert_one(twitter_rec)
        print("Data inserted with record ids", rec_id1)

    except:
        print("Could not insert In Mongo")