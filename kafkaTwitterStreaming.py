# import necessary modules
from tweepy import OAuthHandler
from tweepy.streaming import Stream
from kafka import KafkaProducer

import json
import pickle
import re
# nltk
import nltk

# initializing Lemmatizer and stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

nltk.download('stopwords')
lemma = WordNetLemmatizer()
stop_words = stopwords.words("english")


# define a function to clean the tweet.
def clean_tweet(tweet):
    """
    tweet: String
           Input Data
    tweet: String
           Output Data

    func: Convert tweet to lower case
          Replace URLs with a space in the message
          Replace ticker symbols with space. The ticker symbols are any stock symbol that starts with $.
          Replace  usernames with space. The usernames are any word that starts with @.
          Replace everything not a letter or apostrophe with space
          Remove single letter words
          lemmatize, tokenize (nouns and verb), remove stop words, filter all the non-alphabetic words, then join
          them again

    """

    tweet = tweet.lower()
    tweet = re.sub('((www.[^s]+)|(https?://[^s]+))', ' ', tweet)
    tweet = re.sub('\$[a-zA-Z0-9]*', ' ', tweet)
    tweet = re.sub('[^a-zA-Z\']', ' ', tweet)
    tweet = ' '.join([w for w in tweet.split() if len(w) > 1])

    tweet = ' '.join([lemma.lemmatize(x) for x in nltk.wordpunct_tokenize(tweet) if x not in stop_words])
    tweet = [lemma.lemmatize(x, nltk.corpus.reader.wordnet.VERB) for x in nltk.wordpunct_tokenize(tweet) if
             x not in stop_words]
    return tweet


class TweetListener(Stream):

    # parse json tweet object stream to get desired data
    def on_data(self, data):
        try:
            json_data = json.loads(data)

            send_data = '{}'
            json_send_data = json.loads(send_data)

            # make checks for retweet and extended tweet-->done for truncated text
            if "retweeted_status" in json_data:
                try:
                    json_send_data['text'] = json_data['retweeted_status']['extended_tweet']['full_text']

                except:
                    json_send_data['text'] = json_data['retweeted_status']['text']
            else:
                try:
                    json_send_data['text'] = json_data['extended_tweet']['full_text']
                except:
                    json_send_data['text'] = json_data['text']

            json_send_data['creation_datetime'] = json_data['created_at']
            json_send_data['username'] = json_data['user']['name']
            json_send_data['location'] = json_data['user']['location']
            json_send_data['userDescr'] = json_data['user']['description']
            json_send_data['followers'] = json_data['user']['followers_count']
            json_send_data['retweets'] = json_data['retweet_count']
            json_send_data['favorites'] = json_data['favorite_count']

            # language detection and use of appropriate sentiment analysis module
            txt = json_send_data['text']
            txt = clean_tweet(txt)
            txt = " ".join(txt)
            print(txt)
            txt = vec.transform([txt])
            json_send_data['senti_val'] = str(LRm.predict(txt)[0])
            print(json_send_data)
            producer.send("twitterstream", bytes(json.dumps(json_send_data), 'ascii'))

            return True
        except KeyError:
            return True

    def on_error(self, status):
        print(status)
        return True


with open('f_model.pkl', 'rb') as f:
    (vec, LRm) = pickle.load(f)

producer = KafkaProducer(bootstrap_servers='localhost:9092')

# keywords to look for: commas work as or, words in the same phrase work as and
words = ['Amazon']

# twitter api credentials
consumer_key = 'WpJ7iqIkJUtyJR87oFDfavjRh'
consumer_secret = 'l9DXAKyM8lOq8QZr2AI7LPiT6svKjFskDsLFjjQc7LhudKzgMg'
access_token = '1225697811649286144-B9LOiRnNxCmkI7lOnCx1tNdhAoNXet'
access_secret = 'B4OXNC1d6IErNNQhcN5XRqBCjBaTF5jtModbG7oa12epf'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

# perform activities on stream
twitter_stream = TweetListener(consumer_key, consumer_secret, access_token, access_secret)
twitter_stream.filter(track=words, languages=["en"])
