# Twitter-Sentiment-Analysis-in-Python

## Pipeline Explanation

The pipeline makes use of the twitter streaming API in order to stream tweets in Python in real time, according to specified keywords. The tweets are pushed into a topic in the Kafka cluster by the twitter producer. The streaming twitter data are in JSON format. 

A selection of the relevant fields, as well as simple sentiment analysis, are done during the streaming process. 

On the other end, a MongoDB consumer consumes the streaming data and stores them in MongoDB for future use.
An interactive Dash dashboard prensents live updates of data.

## Code Explanation

The kafkaTwitterStreaming.py script implements the twitter producer.

The kafkaMongoConsumer.py implements the MongoDB consumer.

Finally, the DashboardFinal.py script connects to the Mongo database and presents live results on a simple web dashboard.

## Instructions on Running the Code

The following steps should be followed in order to run the code:
### Machine Preparation
1. Install docker 
2. Install requirements.txt
### Run the Code

1. in the project directory from the cmd line, run: Docker-compose up
2. in an other shell run: python kafkaTwitterStreaming.py 
3. in an other shell run: python kafkaMongoConsumer.py
4. And finally run: python DashboardFinal.py

The results should be showing on an interactive webpage.