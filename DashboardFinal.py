import itertools
import re

import nltk
from pymongo import MongoClient
import plotly.graph_objs as go
import dash
from dash import dcc
import dash.dependencies as dd

from dash import html
from dash.dependencies import Input, Output

from io import BytesIO

import pandas as pd
from wordcloud import WordCloud
import base64


app = dash.Dash()


def create_header(some_string):

    header_style = {
        'background-color' : '#1B95E0',
        'padding' : '1.5rem',
        'color': 'white',
        'font-family': 'Verdana, Geneva, sans-serif'
    }
    header = html.Header(html.H1(children=some_string, style=header_style))
    return header


app.layout = html.Div(children=[


    html.Div(create_header('Real Time Twitter Users Reflections about Amazon ')),
    html.Div([
        html.Div(
            dcc.Graph(
                id='bar',
            ), style={'display': 'inline-block','vertical-align': 'top',  'width': '50%'}),

        html.Div(
            dcc.Graph(
                id='donut-sentiment',
            ), style={'display': 'inline-block','vertical-align': 'top',  'width': '50%'}),
        # html.Div([
        #    html.Img(id="image_wc"),
        # ]),
]
, style={'width': '100%', 'display': 'inline-block'}
            ),
    html.Div([
        html.Div(
            dcc.Graph(
                id='most_words',
            ), style={'display': 'inline-block', 'vertical-align': 'top', 'width': '50%'}),

        html.Div(
            dcc.Graph(
                id='map',
            ), style={'display': 'inline-block', 'vertical-align': 'top', 'width': '50%'}),
        html.Div(
            dcc.Interval(
                id='interval-component',
                interval=5 * 1000,  # in milliseconds
                n_intervals=0
            ))
    ])])

# connect to mongo and store in pandas dataframe
client = MongoClient("mongodb://localhost:27017")
db = client.twitter_amz_DB
collection = db.tweet_info
tweets = pd.DataFrame(list(collection.find()))


# Wordcloud function

def plot_wordcloud(data):

    wc = WordCloud(max_words=1000, width=480, height=360,
                   collocations=False).generate(" ".join(data))
    return wc.to_image()


@app.callback(dd.Output('image_wc', 'src'), [dd.Input('image_wc', 'id')])
def make_image(b):

    data_pos = tweets[tweets['senti_val'] == '1']['text']
    img = BytesIO()
    plot_wordcloud(data=data_pos).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())


# Pie Chart
@app.callback(Output('donut-sentiment', 'figure'),
              [Input('interval-component', 'n_intervals')])
def donut_sentiment(n):

    # bucket the sentimental scores
    cat_senti = []
    for row in tweets.senti_val:
        if int(row) == 1:
            cat_senti.append('Positive')
        elif int(row) == 0:
            cat_senti.append('Negative')
        else:
            cat_senti.append('Neutral')
    tweets['cat_senti'] = cat_senti

    def cal_percent(senti):
        count_net = len(tweets[tweets['cat_senti'] == senti])
        return count_net
    
    data = [cal_percent('Positive'),cal_percent('Negative')]
    #data = [cal_percent('Neutral'),cal_percent('Positive'),cal_percent('Negative')]

    ## Plotting the donut
    trace1 = {"hole": 0.5, "type": "pie", "labels": ["Positive","Negative"], "values": data,
             "showlegend": True, "marker.line.width": 10 , "marker.line.color" : 'white', 'marker': {'colors': ['green','red']}}
    
    layout = go.Layout(
        title = "<b>Sentiments analysis percentage</b>",
        barmode='group',
        titlefont=dict(size=20))
    
    fig = go.Figure(data=[trace1], layout=layout)

    return fig

# Map visualization

@app.callback(Output('map', 'figure'),
              [Input('interval-component', 'n_intervals')])
def map(n):


    # Filter constants for states in US
    STATES = ['Alabama', 'AL', 'Alaska', 'AK', 'American Samoa', 'AS', 'Arizona', 'AZ', 'Arkansas', 'AR', 'California',
              'CA', 'Colorado', 'CO', 'Connecticut', 'CT', 'Delaware', 'DE', 'District of Columbia', 'DC',
              'Federated States of Micronesia', 'FM', 'Florida', 'FL', 'Georgia', 'GA', 'Guam', 'GU', 'Hawaii', 'HI',
              'Idaho', 'ID', 'Illinois', 'IL', 'Indiana', 'IN', 'Iowa', 'IA', 'Kansas', 'KS', 'Kentucky', 'KY',
              'Louisiana', 'LA', 'Maine', 'ME', 'Marshall Islands', 'MH', 'Maryland', 'MD', 'Massachusetts', 'MA',
              'Michigan', 'MI', 'Minnesota', 'MN', 'Mississippi', 'MS', 'Missouri', 'MO', 'Montana', 'MT', 'Nebraska',
              'NE', 'Nevada', 'NV', 'New Hampshire', 'NH', 'New Jersey', 'NJ', 'New Mexico', 'NM', 'New York', 'NY',
              'North Carolina', 'NC', 'North Dakota', 'ND', 'Northern Mariana Islands', 'MP', 'Ohio', 'OH', 'Oklahoma',
              'OK', 'Oregon', 'OR', 'Palau', 'PW', 'Pennsylvania', 'PA', 'Puerto Rico', 'PR', 'Rhode Island', 'RI',
              'South Carolina', 'SC', 'South Dakota', 'SD', 'Tennessee', 'TN', 'Texas', 'TX', 'Utah', 'UT', 'Vermont',
              'VT', 'Virgin Islands', 'VI', 'Virginia', 'VA', 'Washington', 'WA', 'West Virginia', 'WV', 'Wisconsin',
              'WI', 'Wyoming', 'WY']
    STATE_DICT = dict(itertools.zip_longest(*[iter(STATES)] * 2, fillvalue=""))
    INV_STATE_DICT = dict((v, k) for k, v in STATE_DICT.items())
    is_in_US = []
    geo = tweets[['location']]
    df = tweets.fillna(" ")
    for x in df['location']:
        check = False
        for s in STATES:
            if s in x:
                is_in_US.append(STATE_DICT[s] if s in STATE_DICT else s)
                check = True
                break
        if not check:
            is_in_US.append(None)

    geo_dist = pd.DataFrame(is_in_US, columns=['State']).dropna().reset_index()
    geo_dist = geo_dist.groupby('State').count().rename(columns={"index": "Number"}) \
        .sort_values(by=['Number'], ascending=False).reset_index()

    geo_dist['Full State Name'] = geo_dist['State'].apply(lambda x: INV_STATE_DICT[x])
    geo_dist['text'] = geo_dist['Full State Name'] + '<br>' + 'Num: ' + geo_dist['Number'].astype(str)
    fig= go.Figure(go.Choropleth(
        locations=geo_dist['State'],  # Spatial coordinates
        z=geo_dist['Number'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # set of locations match entries in `locations`
        colorscale="Blues",
        text=geo_dist['text'],  # hover text
        showscale=False,
        geo='geo'
    ))


    fig.update_layout(
        geo_scope='usa',title="<b> Distribuation of tweets in USA </b>",
        barmode='group',
        titlefont=dict(size=20)
    )

    return fig


@app.callback(Output('bar', 'figure'),
              [Input('interval-component', 'n_intervals')])
def bar(n):

    tweets['creation_datetime'] = pd.to_datetime(tweets['creation_datetime'])
    '''
    Plot the Line Chart
    '''
    # Clean and transform data to enable time series
    result = tweets.groupby([pd.Grouper(key='creation_datetime', freq='2s'), 'senti_val']).count().unstack(fill_value=0).stack().reset_index()

    result = result.rename(columns={"_id": "Num of amzon mentions", "creation_datetime":"Time in UTC"})
    time_series = result["Time in UTC"][result['senti_val']=='0'].reset_index(drop=True)

    tr1 = go.Scatter(x=time_series,
        y=result["Num of amzon mentions"][result['senti_val']=='0'].reset_index(drop=True),
        name="Negative",
        mode='lines+markers', line_color='#DC6457',
        opacity=0.8)

    tr2 = go.Scatter(
        x=time_series,
        y=result["Num of amzon mentions"][result['senti_val']=='1'].reset_index(drop=True),
        name="Positive",
        mode='lines+markers', line_color='#16D565',
        opacity=0.8)

    layout = go.Layout(
        title='<b> Frequence of sentiments in real time</b>',
        barmode='group',
        titlefont=dict(size=20)
    )


    fig = go.Figure(data=[tr1, tr2], layout=layout)


    return fig


@app.callback(Output('most_words', 'figure'),
              [Input('interval-component', 'n_intervals')])
def most_words(n):

    # extract positive hashtag
    positive = tweets[tweets['senti_val'] == '1']
    positive = positive.apply(lambda x: x.astype(str).str.lower())
    positive_list = positive['text'].tolist()
    positive_sentences_to_string = ''.join(positive_list)
    pos_hash = re.findall(r"#(\w+)", positive_sentences_to_string)

    pos_freq = nltk.FreqDist(pos_hash)
    pos_hash_df = pd.DataFrame({'hashtag': list(pos_freq.keys()),
                                'count': list(pos_freq.values())})
    pos_hash_df = pos_hash_df.sort_values("count", ascending=False)[:10].head(10)

    trace1 = go.Bar(
        x=pos_hash_df['hashtag'],
        y=pos_hash_df['count'],
        name='Top 10 Positive Hashtag',
        marker=dict(color='#1B95E0')  # set the marker color to gold
    )

    data = [trace1]

    layout = go.Layout(
        title='<b>10 Top Hashtags</b>',
        barmode='group',
        titlefont=dict(size=20)
        # 'stack', 'group', 'overlay', 'relative'
    )

    fig = go.Figure(data=data, layout=layout)

    return fig


if __name__ == '__main__':

    app.run_server()
