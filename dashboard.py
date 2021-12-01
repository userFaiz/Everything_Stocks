from hashlib import new
import os
from re import I
from typing import Pattern
#from os import close, link
#from re import X
from requests.models import Response
import streamlit as st
import pandas as pd
import numpy as np
import requests
import tweepy
from tweepy.api import API
import yfinance as yf
import config
from datetime import date, datetime, time, timedelta
import plotly
from plotly import graph_objs as go
#from bs4 import BeautifulSoup
#from urllib.request import Request, urlopen
#from requests_html import HTMLSession
#from pygooglenews import GoogleNews
#from psaw import PushshiftAPI
import datetime
from newsapi.newsapi_client import NewsApiClient
import yahoo_fin.stock_info as si
from yahoo_fin.stock_info import get_data, get_quote_table
import time
import pandas_datareader as pdr
#import talib
import ta
from PIL import Image

st.set_page_config(layout="wide")


pd.options.mode.chained_assignment = None
#pd.options.mode.chained_assignment = None

yf.pdr_override()

#API's
newsapi = NewsApiClient(api_key=st.secrets["NEWSapi_key"])
auth = tweepy.OAuthHandler(st.secrets["TWITTER_CONSUMER_KEY"], st.secrets["TWITTER_CONSUMER_SECRET"])
auth.set_access_token(st.secrets["TWITTER_ACSESS_TOKEN"], st.secrets["TWITTER_ACSESS_TOKEN_SECRET"])
api = tweepy.API(auth, wait_on_rate_limit = True)

#START = pd.datetime.strptime((date.today() - timedelta(60)).strftime("%Y-%m-%d"), "%Y-%m-%d") 
#TODAY = pd.datetime.strptime((date.today()).strftime("%Y-%m-%d"), "%Y-%m-%d")
#dt = pd.bdate_range(start=START, end=TODAY, freq="D")


START = (date.today() - timedelta(213)).strftime("%Y-%m-%d")
TODAY = (date.today()).strftime("%Y-%m-%d")
#date_updated = date.today()

#START = "2020-04-12" 
#TODAY = "2020-11-12"

#Sidebar
st.sidebar.title("Navigation Menu")
tabs = st.sidebar.selectbox("Go To: ", ( 'Home', 'Twitter Recommendations', 'Our Recommendations', 'Credits' ))

@st.cache
def load_data(ticker):
    yfdata = yf.download(tickers = ticker, start = userStart, end = userEnd)
    yfdata.reset_index(inplace = True)
    yfdata['Date'] = pd.to_datetime(yfdata['Date']).dt.strftime("%Y-%m-%d")
    #if yfdata['Date'].dt.weekday() < 5:

    #yfdata['Date'] = yfdata['Date'][4:]
    return yfdata

@st.cache(allow_output_mutation=True,suppress_st_warning=True)
def load_data_reg(ticker):
    yfdata = yf.download(tickers = ticker, start = START, end = TODAY)
    yfdata.reset_index(inplace = True)
    yfdata['Date'] = pd.to_datetime(yfdata['Date']).dt.strftime("%Y-%m-%d")
    #if yfdata['Date'].dt.weekday() < 5:

    #yfdata['Date'] = yfdata['Date'][4:]
    return yfdata

@st.cache
def update_csv(symbols):
    ##for symbol in symbols:
    ##data = yf.download(tickers = symbols, threads = True, start = START , end = TODAY )
    ##data = pdr.get_data_yahoo(symbols, start = START , end = TODAY)
    #data = get_data(symbols, start_date=START, end_date=TODAY)
    #for symbol in symbols:
        #data = si.get_data(symbol)
        #data.to_csv('DataSet/dailydata/{}.csv'.format(symbol))
        ##### start=START, end=TODAY
    data = yf.download(symbols, group_by='ticker', start=START, end=TODAY, thread = True, proxy = None, auto_adjust = False, prepost = False)
    ##data.reset_index(inplace = True)
    ##data = data.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1)
    ##st.write(data)
    ##st.write(data['A']['Close'])
    for symbol in symbols:
        data[symbol].to_csv('DataSet/dailyData/{}.csv'.format(symbol))


def is_consolidating(df, percentage = 2):
    recent_candlesticks = df[-15:]

    max_close = recent_candlesticks['Close'].max()
    min_close = recent_candlesticks['Close'].min()

    threshold = 1 - (percentage / 100)
    if min_close > (max_close * threshold):
        return True

    return False


def is_breaking_out(df, percentage = 2.5):
    last_close = df[-1:]['Close'].values[0]
    
    if is_consolidating(df[:-1], percentage=percentage):
        recent_closes = df[-16:-1]

        if last_close > recent_closes['Close'].max():
            return True

    return False

@st.cache
def plot_raw_data():
    fig = go.Figure()
    fig.update_yaxes(title_text = 'Price')
    fig.update_xaxes(title_text = 'Dates (slide to zoom)')
    fig.add_trace(go.Scatter(x=graphdata['Date'], y=graphdata['Open'], name = 'Stock Open'))
    fig.add_trace(go.Scatter(x=graphdata['Date'], y=graphdata['Close'], name = 'Stock Close'))
    fig.layout.update(title_text = 'Real Time Graph of ' + "$" + sym.upper(), xaxis_rangeslider_visible =True)
    #fig.update_layout(xaxis_tickformat = "%Y")
    #fig.update_xaxes(type='category', tick0 = 150, dtick = 250)
    return (fig)

@st.cache
def plot_candle_data(graphdata,sym):
    fig = go.Figure(data=[go.Candlestick(x=graphdata['Date'], open = graphdata['Open'], high = graphdata['High'], low = graphdata['Low'], close = graphdata['Close'])])
    fig.update_yaxes(title_text = 'Price')
    fig.update_xaxes(title_text = 'Dates (slide to zoom)')
    fig.layout.update(title_text = 'Real Time Graph of ' + "$" + sym.upper(), xaxis_rangeslider_visible =True)
    fig.update_layout(xaxis_tickformat = "%Y")
    fig.update_xaxes(type='category', tick0 = 10, dtick = 19)
    return (fig)

@st.cache
def plot_sma_data(df,sym):
    candlestick = go.Candlestick(x=df['Date'], open = df['Open'], high = df['High'], low = df['Low'], close = df['Close'])
    upper_band =  go.Scatter(x=df['Date'], y=df['upper_band'], name = 'Upper Bollinger Band', line={'color': 'red'})
    lower_band = go.Scatter(x=df['Date'], y=df['lower_band'], name = 'Lower Bollinger Band', line={'color': 'red'})
    upper_keltner =  go.Scatter(x=df['Date'], y=df['upper_keltner'], name = 'Upper Keltner Channel', line={'color': 'blue'})
    lower_keltner = go.Scatter(x=df['Date'], y=df['lower_keltner'], name = 'Lower Keltner Channel', line={'color': 'blue'})
    #final_upper = go.Scatter(x=df2['Date'], y=df2['upperband'], name = 'Sell Line', line = {'color': 'red'})
    #final_lower = go.Scatter(x=df2['Date'], y=df2['lowerband'], name = 'Buy Line', line = {'color': 'green'})
    #final_upper, final_lower
    fig = go.Figure(data=[candlestick,upper_band,lower_band, upper_keltner, lower_keltner])
    fig.layout.update(title_text = 'Real Time Graph of ' + "$" + sym.upper())
    fig.update_layout(xaxis_tickformat = "%Y")
    fig.update_xaxes(type='category', tick0 = 10, dtick = 19)
    return (fig)

#@st.cache(allow_output_mutation=True,suppress_st_warning=True)
def write_chart_sma(i):
    df = load_data_reg(i)
    df = squeeze_load_data(df)
    df['squeeze_on'] = df.apply(in_squeeze, axis = 1)
    chart = plot_sma_data(df,i)
    return chart

#@st.cache(allow_output_mutation=True,suppress_st_warning=True)
def write_reg_chart(i):
    #st.write(i)
    sym = i
    graphdata = load_data_reg(sym)
    chart = plot_candle_data(graphdata,sym)
    return chart

def sort_helper(list):
    value = []
   #st.write(list)
    #count = 0
    for i in list:
        info = load_data_reg(i)
        #if i == "K":
            #st.write(info)
        vol = info.iloc[-1]['Volume']

        if np.isnan(vol):
            vol = info.iloc[-2]['Volume']

        value.append((i,vol))
    #st.write(value)


    #c = [x+[y] for x, y in zip(str(list[i]), value)]
    return value

def sort_key(list):
    return list[1]

def squeeze_load_data(df):
    df['20sma'] = df['Close'].rolling(window = 20).mean()
    df['stdev'] = df['Close'].rolling(window=20).std()
    df['lower_band'] = df['20sma'] - (2 * df['stdev'])
    df['upper_band'] = df['20sma'] + (2 * df['stdev'])
    df['TR'] = abs(df['High'] - df['Low'])
    df['ATR'] = df['TR'].rolling(window=20).mean()
    df['lower_keltner'] = df['20sma'] - df['ATR'] * 1.5
    df['upper_keltner'] = df['20sma'] + df['ATR'] * 1.5
    return df


def tr(df2):
    df2['previous_close'] = df2['Close'].shift(1)
    df2['high-low'] = df2['High'] - df2['Low']
    df2['high-pc'] = abs(df2['High'] - df2['previous_close'])
    df2['low-pc'] = abs(df2['Low'] - df2['previous_close'])
    tr = df2[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    return tr


def atr(df2, period=14):
    df2['tr'] = tr(df2)
    the_atr = df2['tr'].rolling(period).mean()
    return the_atr


def supertrend(df2,period=7, multiplier=3):
    df2['atr'] = atr(df2, period=period)
    df2['upperband'] = ((df2['High'] + df2['Low']) / 2) + (multiplier * df2['atr'])
    df2['lowerband'] = ((df2['High'] + df2['Low']) / 2) - (multiplier * df2['atr'])
    df2['in_uptrend'] = True

    for current in range(1, len(df2.index)):
        previous = current -1

        if df2['Close'][current] > df2['upperband'][previous]:
            df2['in_uptrend'][current] = True
        elif df2['Close'][current] < df2['lowerband'][previous]:
            df2['in_uptrend'][current] = False
        else:
            df2['in_uptrend'][current] = df2['in_uptrend'][previous]

            if df2['in_uptrend'][current] and df2['lowerband'][current] < df2['lowerband'][previous]:
                df2['lowerband'][current] = df2['lowerband'][previous]

            if not df2['in_uptrend'][current] and df2['upperband'][current] > df2['upperband'][previous]:
                df2['upperband'][current] = df2['upperband'][previous]
    
    return df2


def in_squeeze(df):
    return df['lower_band'] > df['lower_keltner'] and df['upper_band'] < df['upper_keltner']

if tabs == 'Credits':
    image = Image.open('credits.jpeg')
    col1, col2, col3= st.columns([.4,1,.5])
    col2.image(image, width=400)
    st.header("Creator: Faiz Bhimji")
    st.subheader("About Me: ")
    st.write("Everything-Stocks is a side project I made by myself because I was tired of having 10-20 different web pages open when trading stocks just to get the information I need. I decided to make Everything-Stocks becasue I wanted a one website that would give me everything I need to be able to trade. I also made this as a avenue to showcase my python skills and see what all I can do with what I know. I learned so much throughout this project and am definetly happy with the result. Overtime, I hope to improve this platform by enhancing the stock recommendation algorithm, and also enhancing various site features. I hope you enjoy the site! Everything-Stocks is still in beta so I would love to hear about any issues or suggestions you might have for me to improve on!")
    st.write("Contact: Email: faizstock@gmail.com or message me on Linkin: www.linkedin.com/in/faiz-bhimji ")
    st.subheader("The Data: ")
    st.write("I scraped information about stocks off of Twitter, Yahoo, Google, StockTwits, and imported data from various sources listed in my [GitHub](https://github.com/userFaiz/Everything_Stocks).")


if tabs == 'Our Recommendations':
    image = Image.open('boom.jpeg')
    col1, col2, col3= st.columns([.4,1,.5])
    col2.image(image, width=400)
    col1, col2, col3= st.columns([.4,1.5,.3])
    col2.title("Our Recommendations")
    reccomended = st.selectbox("Use the dropdown to navigate between watchlist and breakout candidates", ("Breakout Candidates", "Watchlist of Future Breakouts"))
    consolidating, breakingOut, in_the_squeeze, breaking_out_squeeze, consolidating_in_squeeze = [],[],[],[],[]
    dfSp = si.tickers_sp500()
    st.write("Our Stock Finding Algorithm uses two popular stock indicators (SuperTrend, and TTM Squeeze), which we translated to code in python. The Algorithm then screens the market for any stocks in position to break out. We take these results and then sort the stocks by volume to accurately gauge breakout potential. Click the Run Algorithm button below to start scanning for stocks using real time market data.")
    col1, col2, col3= st.columns([1,1,.5])
    alg_button = col2.button("Run Algorithm")
    if alg_button:
        msg = st.text("Fetching Today's Breakout List...(This may take a few minutes depending on your interent connection)")
        start = time.time()
        update_csv(dfSp)
        for filename in os.listdir('DataSet/dailyData'):

            df = pd.read_csv('DataSet/dailyData/{}'.format(filename))

            if df.empty:
                continue

            df2 = df

            df = squeeze_load_data(df)

            df['squeeze_on'] = df.apply(in_squeeze, axis = 1)

            try:
                if is_consolidating(df, percentage=2.5):
                    if not df.iloc[-3]['squeeze_on']:
                        consolidating.append(filename[:-4])
                        continue

                if df.iloc[-3]['squeeze_on'] and df.iloc[-1]['squeeze_on']:
                    if is_consolidating(df,percentage=2.5):
                        consolidating_in_squeeze.append(filename[:-4])
                        continue

                    if (not is_breaking_out(df)):
                        if not is_consolidating(df, percentage=2.5):
                            in_the_squeeze.append(filename[:-4])
                            continue
                        
                if (df.iloc[-3]['squeeze_on']) and (not df.iloc[-1]['squeeze_on']):
                    superdata = supertrend(df2)
                    if superdata.iloc[-3]['in_uptrend']:
                        breaking_out_squeeze.append(filename[:-4])
                        continue
                    
                if is_breaking_out(df):
                    superdata = supertrend(df2)
                    if superdata.iloc[-3]['in_uptrend']:
                        breakingOut.append(filename[:-4])
                        continue

            except:
                continue

        if reccomended == "Breakout Candidates":
            #st.write(newList)
            
            #col1, col2 = st.columns([1,1])
            #msg = st.text("Fetching Today's List...(This may take a few minutes depending on your interent connection)")
            if breakingOut:
                st.subheader("Stocks Breaking Out: ")
                #st.write(breakingOut)
                newList = sort_helper(breakingOut)
                newList.sort(key=sort_key, reverse=True)
                for i in newList:
                    if newList.index(i) > 10:
                        break
                    chart = write_reg_chart(i[0])
                    st.write(i[0])
                    st.plotly_chart(chart)

            if breaking_out_squeeze:
                st.subheader("Stocks breaking out the squeeze: ")
                #st.write(breaking_out_squeeze)
                #msg.text("Uploaded!")
                bsquesse = sort_helper(breaking_out_squeeze)
                bsquesse.sort(key=sort_key, reverse=True)
                for i in bsquesse:
                    if bsquesse.index(i) > 10:
                        break
                    chart = write_chart_sma(i[0])
                    st.write(i[0])
                    st.plotly_chart(chart)
                msg.text("List Uploaded!")

        if reccomended == "Watchlist of Future Breakouts":
            userStart = date.today() - timedelta(100)
            userEnd = date.today()
            msg.text("Fetching Today's Watch List...(This may take a few minutes depending on your interent connection)")
            #st.write(in_the_squeeze)
            
            if consolidating_in_squeeze:
                #button_squeeze_consol = st.button("Good Breakout Potential")
                #if button_squeeze_consol:
                    st.subheader("Stocks Consolidating in the squeeze: ")
                    newLister = sort_helper(consolidating_in_squeeze)
                    newLister.sort(key=sort_key, reverse=True)
                    for i in newLister:
                        if newLister.index(i) > 10:
                            break
                        chart = write_chart_sma(i[0])
                        st.write(i[0])
                        st.plotly_chart(chart)

            if consolidating:
                #button_consol = st.button("Great Setup for Breakout")
                #if button_consol:
                st.subheader("Stocks Consolidating: ")
                #st.write(consolidating)
                consol_lister = sort_helper(consolidating)
                consol_lister.sort(key=sort_key, reverse=True)
                #st.write(consol_lister)
                for i in consol_lister:
                    if consol_lister.index(i) > 10:
                        break
                    #chart = write_chart_sma(i[0]) 
                    chart = write_reg_chart(i[0])
                    st.write(i[0])
                    st.plotly_chart(chart)
            
            if in_the_squeeze:
                #button_squeeze = st.button("On the Right Track")
                #if button_squeeze:
                st.subheader("Stocks In the Squeeze")
                    #st.write(in_the_squeeze)
                newl = sort_helper(in_the_squeeze)
                newl.sort(key=sort_key, reverse=True)
                for i in newl:
                    if newl.index(i) > 10:
                        break
                    chart = write_chart_sma(i[0]) 
                    st.write(i[0])
                    st.plotly_chart(chart)
            msg.text("List Uploaded!")

    #st.write(, breakingOut, in_the_squeeze, consolidating_in_squeeze, breaking_out_squeeze)
        st.write("Done! the program took {} seconds".format(time.time()-start))

if tabs == 'Twitter Recommendations':
    image = Image.open('street.jpeg')
    col1, col2, col3= st.columns([.4,1,.5])
    col2.image(image, width=400)
    col1, col2, col3= st.columns([.4,1.5,.5])
    col2.title("Twitter Recommendations")
    st.write("Get all recent stock callouts from your favorite Twitter Traders, we sort through all the retweets and non stock related posts to only display the most recent stock callouts and a real time graph of the stock")
    st.write("Some Twitter Traders we Recommend Are:  traderstewie, Maximus_Holla, and DonnieStocks")
    TWITTER_USERNAMES = []
    userFavTrader = st.text_input("Please enter the '@' of the account you would like to parse through.")
    message = st.text("Don't Include the '@' When Entering the Account, and One Account at a Time Please")
    TWITTER_USERNAMES.append(userFavTrader)
    #col1, col2 = st.columns([2,1])
    for username in TWITTER_USERNAMES:
        try:
            user = api.get_user(screen_name = username)
            valid = True
            message.text("Successfully Added!")
        except:
            valid = False
            if userFavTrader == "":
                message.text("Don't Include the '@' When Entering the Account, and One Account at a Time Please")
            else:
                message.text("USERNAME INVALID please check their @ and try again")
        if valid:
            tweets = api.user_timeline(screen_name = username, exclude_replies = True, include_rts = False, tweet_mode = 'extended')
            st.image(user.profile_image_url, output_format='auto')
            st.subheader("User: " + '@' + user.screen_name + " tweeted: ")
            for tweet in tweets:
                if '$' in tweet.full_text:
                    #st.write(tweet)
                    #tweet.truncated = True
                    words = tweet.full_text.split(' ')
                    for word in words:
                        if word.startswith('$') and word[1:].isalpha():
                            sym = word[1:]
                            st.write(tweet.full_text)
                            userStart = date.today() - timedelta(40)
                            userEnd = date.today()
                            #st.write("Graph Of " + word +  ": ")
                            #st.image(f"https://finviz.com/chart.ashx?t={sym}")
                            graphdata = load_data_reg(sym)
                            chart = plot_candle_data(graphdata,sym)
                            st.plotly_chart(chart)
                            st.write((tweet.created_at).strftime("Tweet Posted: %h-%d-%Y" + " at " "%H:%M"))
                            st.text("----------------------------")



if tabs == 'Home':
    col1, col2, col3= st.columns([.6,1.5,.5])
    col2.title("Everything-Stocks")
    image = Image.open('stock.webp')
    col1, col2, col3= st.columns([.4,1,.5])
    col2.image(image, width=400)
    #col2.image(image)
    st.subheader("The One Stop Shop For All Things Stocks!")
    success = True
    try:
        sym = st.text_input("Ticker Symbol", value ='', max_chars=5)

        #TEST IF SYMBOL IS VALID
        rtest = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{sym}.json")
        test = rtest.json()
        testnuk = test['messages']

        userStart = (st.date_input("Graph Start Date: (Click To Change) ", value = pd.to_datetime("2016-01-01")))
        userEnd = (st.date_input("Graph End Date: (Click To Change) ", value = pd.to_datetime("today")))
        #st.write(userStart)
        data_load_state = st.text("Retrieving Data...")
        graphdata = load_data(sym)
        data_load_state.text("Data Uploaded!")

        col1, col2, col3, col4 = st.columns([.4,1,1,1])


        chart = plot_raw_data()
        col2.plotly_chart(chart)
        #info = yf.Ticker(sym).stats()

        col1, col2, col3,col4 = st.columns([.5,1,1,1.4])

        buttonData = col2.button("$" + sym.upper() + " Raw Data ")
        if buttonData:
            nameDate = st.subheader('Data' + " from " + userStart.strftime("%h-%d-%Y") + " to " + userEnd.strftime("%h-%d-%Y"))
            writtenDate = st.write(graphdata)
            if st.button("Hide Raw Data"):
                nameDate.text("")
                writtenDate.text("")

        buttonInfo = col3.button("About " "$" + sym.upper())
        if buttonInfo:
            info = yf.Ticker(sym).stats()
            ##st.write(info['summaryProfile'])
            st.subheader("About " + "$" + sym.upper() + ": ")
            #st.write(info)
            sector = st.write("Sector: " + info['summaryProfile']["sector"])
            industry = st.write("Industry: " + info['summaryProfile']["industry"])
            summary = st.write((info['summaryProfile']["longBusinessSummary"]))
            if st.button("Hide Company Information"):
                sector.text("")
                industry.text("")
                summary.text("")
        butt_rec = col4.button("Market Recommendations")
        #st.write(str(info['recommendationTrend']["trend"][3]['strongBuy']))
        if butt_rec:
            info = yf.Ticker(sym).stats()
            st.subheader("Market Recommendations on " + "$" + sym.upper() + ": ")
            #st.write(info)
            #text = info['recommendationTrend']["trend"][3]
            strongBuy = st.write("Strong Buy: " + str(info['recommendationTrend']["trend"][3]['strongBuy']))
            buy = st.write("Buy: " + str(info['recommendationTrend']["trend"][3]['buy']))
            hold = st.write(("Hold: " + str(info['recommendationTrend']["trend"][3]['hold'])))
            sell= st.write(("Sell: " + str(info['recommendationTrend']["trend"][3]['sell'])))
            if st.button("Hide Market Recommendations"):
                strongBuy.text(" ")
                buy.text("")
                hold.text("")
                sell.text("")
    except:
        if sym == "":
            st.text("Please Enter a Ticker Symbol")
            success = False
        else:
            st.text("This Ticker Symbol is Not Supported Please Try Again.")
            success = False

    if(success):
        st.subheader("Recent " + "$" + sym.upper() + " News: ")
        option = st.selectbox("Select an option below to see the latest on "+ "$" + sym.upper(),('Please Select', 'News Articles', 'Twitter', 'StockTwits'))
        
        if option == 'Please Select':
            #"The Latest on " + "$" + sym.upper()
            st.text("")

        if option == 'Twitter':
            st.subheader("What Twitter Users Are Saying About " + "$" + sym.upper() + ": ")
            claim = st.text("Please Choose How You Want Your Data To Be Sorted: ")
            col1, col2 = st.columns([1,3])
            recentButton = col2.button("Most Recent")
            if recentButton:
                claim.text("")
                ans = 'recent'
                query = ('$'+ sym)
                cursor = tweepy.Cursor(api.search_tweets, q = query, tweet_mode = 'extended', result_type = ans).items(200)
                for i in cursor:
                    #st.write(dir(i))
                    if not (i.retweeted) and ('RT @' not in i.full_text):
                        usr = i.user
                        st.image(usr.profile_image_url, output_format='auto')
                        st.subheader("User: " + '@' + usr.screen_name + " tweeted: ")
                        st.write((i.full_text))
                        st.write((i.created_at).strftime("Tweet Posted: %h-%m-%Y" + " at " "%H:%M"))
                        st.text("----------------------------")


            #popularButton = col3.button("Most Popular")
            #if popularButton:
                #claim.text("")
                #ans = 'popular'
                #query = ('$'+ sym)
                #cursor = tweepy.Cursor(api.search_tweets, q = query, tweet_mode = 'extended', result_type = ans).items(200)
                #for i in cursor:
                    #if not (i.retweeted) and ('RT @' not in i.full_text):
                        #usr = i.user
                        #st.image(usr.profile_image_url, output_format='auto')
                        #st.subheader("User: " + '@' + usr.screen_name + " tweeted: ")
                        #st.write((i.full_text))
                        #st.write((i.created_at).strftime("Tweet Posted: %h-%m-%Y" + " at " "%H:%M"))
                        #st.text("----------------------------")


            mixedButton = col1.button("Most Popular")
            if mixedButton:
                claim.text("")
                ans = 'mixed'
                query = ('$'+ sym)
                cursor = tweepy.Cursor(api.search_tweets, q = query, tweet_mode = 'extended', result_type = ans).items(200)
                for i in cursor:
                    if not (i.retweeted) and ('RT @' not in i.full_text):
                        usr = i.user
                        st.image(usr.profile_image_url, output_format='auto')
                        st.subheader("User: " + '@' + usr.screen_name + " tweeted: ")
                        st.write((i.full_text))
                        st.write((i.created_at).strftime("Tweet Posted: %h-%m-%Y" + " at " "%H:%M"))
                        st.text("----------------------------")

        if option == 'StockTwits':
            r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{sym}.json")
            data = r.json()
            st.subheader("What StockTwit Users Are Saying About " + "$" + sym.upper() + ": ")
            st.text("Listing Sorted by Most Recent: ")
            for message in data['messages']:
                st.subheader("")
                st.image(message['user']['avatar_url'])
                st.subheader('User: ' + message['user']['username'])
                st.write('  ' + message['body'])
                t = message['created_at']
                st.text("---------------------")
                st.text('Posted on: ' + (t[5:8] + t[8:10] + '-' + t[0:4]))
                st.text('Local Time: ' +  t[11:19])
                st.text(" ")
                st.text("---------------------")

        if option == 'News Articles':
            info = yf.Ticker(sym).stats()
            st.subheader("Recent Articles Published About " + "$" + sym.upper() + ": ")
            selection = st.text("Please Choose How You Want Your Data To Be Sorted: ")
            col1, col2, col3 = st.columns([1,1,.6])

            rel = col1.button("Sort By Relevance ")
            fresh = col2.button("Sort By Newest ")
            pop = col3.button("Sort By Popularity ")

            sorter = 'publishedAt'

            if rel:
                query = ('$'+ sym)
                selection.text("")
                name = info['price']["shortName"]
                name = name.split()[0]
                sorter = 'relevancy'
                yesterday = date.today() - timedelta(30)
                all_articles = newsapi.get_everything(qintitle = (name),
                                      from_param = yesterday,
                                      to = date.today(),
                                      language='en',
                                      sort_by = sorter,
                                      page_size= 100)
            
                results = all_articles["totalResults"]
                list_of_articles = all_articles["articles"]
                ##st.write(list_of_articles)
                st.subheader("Total Results: " + str(results))
                for item in list_of_articles:
                    try:
                        #st.write(item['author'])
                        #st.write(item['source']['name'])
                        #st.write()
                        st.image(item['urlToImage'])
                        st.write("Author: " + str((item['author'])) + " - " + str((item['source']['name'])))
                        st.write("Title of article: " + str(item['title']))
                        published = str(item['publishedAt'])
                        st.write("Published On: " + str(published[0:10])+ ", Time: " + str(published[11:16]))
                        st.write("Link to article: " + item["url"])
                    except:
                        continue
    
            if fresh:
                query = ('$'+ sym)
                selection.text("")
                name = info['price']["shortName"]
                name = name.split()[0]
                sorter = 'publishedAt'
                yesterday = date.today() - timedelta(30)
                all_articles = newsapi.get_everything(qintitle = (name),
                                      from_param = yesterday,
                                      to = date.today(),
                                      language='en',
                                      sort_by = sorter,
                                      page_size= 100)
            
                results = all_articles["totalResults"]
                list_of_articles = all_articles["articles"]
                ##st.write(list_of_articles)
                st.subheader("Total Results: " + str(results))
                for item in list_of_articles:
                    try:
                        #st.write(item['author'])
                        #st.write(item['source']['name'])
                        #st.write()
                        st.image(item['urlToImage'])
                        st.write("Author: " + str((item['author'])) + " - " + str((item['source']['name'])))
                        st.write("Title of article: " + str(item['title']))
                        published = str(item['publishedAt'])
                        st.write("Published On: " + str(published[0:10])+ ", Time: " + str(published[11:16]))
                        st.write("Link to article: " + item["url"])
                    except:
                        continue
            if pop:
                query = ('$'+ sym)
                name = info['price']["shortName"]
                name = name.split()[0]
                selection.text("")
                sorter = 'popularity'
                yesterday = date.today() - timedelta(30)
                all_articles = newsapi.get_everything(qintitle = (name),
                                      from_param = yesterday,
                                      to = date.today(),
                                      language='en',
                                      sort_by = sorter,
                                      page_size= 100)
            
                results = all_articles["totalResults"]
                list_of_articles = all_articles["articles"]
                ##st.write(list_of_articles)
                st.subheader("Total Results: " + str(results))
                for item in list_of_articles:
                    try:
                        #st.write(item['author'])
                        #st.write(item['source']['name'])
                        #st.write()
                        st.image(item['urlToImage'])
                        st.write("Author: " + str((item['author'])) + " - " + str((item['source']['name'])))
                        st.write("Title of article: " + str(item['title']))
                        published = str(item['publishedAt'])
                        st.write("Published On: " + str(published[0:10])+ ", Time: " + str(published[11:16]))
                        st.write("Link to article: " + item["url"])
                    except:
                        continue
            #yesterday = date.today() - timedelta(3)
            #all_articles = newsapi.get_everything(q='$' + sym,
                                      #from_param = yesterday,
                                      #to = date.today(),
                                      #language='en',
                                      #sort_by = sorter)
            
            #results = all_articles["totalResults"]
            #list_of_articles = all_articles["articles"]
            #st.write(list_of_articles)
            #st.subheader("Total Results: " + str(results))
            #for item in list_of_articles:
                #st.image(item['urlToImage'])
                #st.write("Author: " + item['author'] + " - " + item['source']['name'] )
                #st.write("Title of article: " + item['title'])
                #published = item['publishedAt']
                #st.write("Published On: " + published[0:10]+ ", Time: " + published[11:16])
                #st.write("Link to article: " + item['url'])






            #googlenews = GoogleNews(lang = 'en', region = 'US')
            #googlenews.set_period('1d')
            #result = googlenews.search(sym)
            #st.write(result)
            
            #gn = GoogleNews(lang = 'en', country =' US')
            #def get_titles(search):
                #search = gn.search('$' + sym, when = '1d')
                #news = search['entries']
                #for item in news:
                    #st.subheader(item.source.title + " Says: ")
                    #st.write(item.title)
                    #st.write(item.link)
                    #st.write(item.published)

                   
            #newss = (get_titles(sym))
                
            #search = gn.search(sym, when = '1d')
            #st.write(search['entries'])




        #if option == 'WallStreetBets':
            ##def to_integer(dt_time):
                ##return 10000*dt_time.year + 100*dt_time.month + dt_time.day

            #api = PushshiftAPI()
            #yesterday = date.today() - timedelta(3)
            ##st.write(yesterday)
            #year = yesterday.year
            #month = yesterday.month
            #day = yesterday.day

            #start_time = int(datetime.datetime(year, month, day).timestamp())

            #submissions = api.search_submissions(after=start_time, subreddit='wallstreetbets', filter=['url','author', 'title', 'subreddit'])
            #for submission in submissions:
                #words = submission.title.split()
                #cashtags = list(set(filter(lambda word: word.lower().startswith('$') and word[1:].isalpha(), words)))
                #for item in cashtags:
                    #if len(cashtags) > 0:
                        #if item.lower() == ('$'+ sym.lower()):
                            ##st.write(cashtags)
                            #st.write("User Name: "+ submission.author)
                            #st.write(submission.title)
                            #st.write(submission.url)
                    #else:
                        #st.text("No recent results found on WSJ for " + '$'+ sym)


                
