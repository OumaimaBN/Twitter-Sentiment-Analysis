# Libraries importing
import itertools
import re
import nltk
from pymongo import MongoClient
import plotly.graph_objs as go
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd

# Dash application
app = dash.Dash()


def create_header(title):
    """
     Create the header of the web page
    :param title:
    :return:
    """

    header_style = {
        'background-color': '#1B95E0',
        'padding': '1.5rem',
        'color': 'white',
        'font-family': 'Verdana, Geneva, sans-serif'
    }
    header = html.Header(html.H1(children=title, style=header_style))
    return header


app.layout = html.Div(children=[

    html.Div(create_header('Real Time Twitter Users Reflections about Amazon ')),

    html.Div([
        html.Div(
            dcc.Graph(
                id='timeseries_sentiment',
            ), style={'display': 'inline-block', 'vertical-align': 'top', 'width': '50%'}),

        html.Div(
            dcc.Graph(
                id='donut-sentiment',
            ), style={'display': 'inline-block', 'vertical-align': 'top', 'width': '50%'}),
    ], style={'width': '100%', 'display': 'inline-block'}),

    html.Div([
        html.Div(
            dcc.Graph(
                id='most_words',
            ), style={'display': 'inline-block', 'vertical-align': 'top', 'width': '50%'}),

        html.Div(
            dcc.Graph(
                id='map_viz',
            ), style={'display': 'inline-block', 'vertical-align': 'top', 'width': '50%'}),

        html.Div(
            dcc.Interval(
                id='interval-component',
                interval=5 * 1000,  # in milliseconds
                n_intervals=0
            ))
    ])])

# connect to mongo1 and store in pandas dataframe
client = MongoClient("mongodb://localhost:27017")
db = client.twitter_amz_DB
collection = db.tweet_info
tweets = pd.DataFrame(list(collection.find()))


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

    def cal_percent(sentiment_label):
        """
        compute the total count of a sentiment label
        :param sentiment_label:
        :return: count
        """
        count_net = len(tweets[tweets['cat_senti'] == sentiment_label])
        return count_net

    data = [cal_percent('Positive'), cal_percent('Negative')]

    # Plotting the donut
    trace1 = {"hole": 0.5, "type": "pie", "labels": ["Positive", "Negative"], "values": data,
              "showlegend": True, "marker.line.width": 10, "marker.line.color": 'white',
              'marker': {'colors': ['green', 'red']}}

    layout = go.Layout(
        title="<b>Sentiments analysis percentage</b>",
        barmode='group',
        titlefont=dict(size=20))

    fig = go.Figure(data=[trace1], layout=layout)

    return fig


# Map visualization
@app.callback(Output('map_viz', 'figure'),
              [Input('interval-component', 'n_intervals')])
def map_viz(n):

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
    fig = go.Figure(go.Choropleth(
        locations=geo_dist['State'],  # Spatial coordinates
        z=geo_dist['Number'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # set of locations match entries in `locations`
        colorscale="Blues",
        text=geo_dist['text'],  # hover text
        showscale=False,
        geo='geo'
    ))

    fig.update_layout(
        geo_scope='usa', title="<b> Distribuation of tweets in USA </b>",
        barmode='group',
        titlefont=dict(size=20)
    )

    return fig


@app.callback(Output('timeseries_sentiment', 'figure'),
              [Input('interval-component', 'n_intervals')])
def timeseries_sentiment(n):
    tweets['creation_datetime'] = pd.to_datetime(tweets['creation_datetime'])
    '''
    Plot the Line Chart
    '''
    # Clean and transform data to enable time series
    result = tweets.groupby([pd.Grouper(key='creation_datetime', freq='2s'), 'senti_val']).count().unstack(
        fill_value=0).stack().reset_index()

    result = result.rename(columns={"_id": "Num of amazon mentions", "creation_datetime": "Time in UTC"})
    time_series = result["Time in UTC"][result['senti_val'] == '0'].reset_index(drop=True)

    tr1 = go.Scatter(x=time_series,
                     y=result["Num of amazon mentions"][result['senti_val'] == '0'].reset_index(drop=True),
                     name="Negative",
                     mode='lines+markers', line_color='#DC6457',
                     opacity=0.8)

    tr2 = go.Scatter(
        x=time_series,
        y=result["Num of amazon mentions"][result['senti_val'] == '1'].reset_index(drop=True),
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
        marker=dict(color='#1B95E0')  # set the marker color
    )

    data = [trace1]

    layout = go.Layout(
        title='<b>10 Top Hashtags</b>',
        barmode='group',
        titlefont=dict(size=20)
    )

    fig = go.Figure(data=data, layout=layout)

    return fig


if __name__ == '__main__':
    app.run_server()
