import time
import requests
import urllib.parse
import hashlib
import hmac
import base64
from pathlib import Path
from termcolor import colored
import os
import json
import traceback

import datetime

import krakenex


api_url = "https://api.kraken.com"
api_key = Path('./kraken_api_key.txt').read_text()
private_key = Path('./kraken_api_private_key.txt').read_text()
k = krakenex.API(api_key, private_key)  # use for getting market data
def get_kraken_signature(urlpath, data, secret):  # use for making orders
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()


def kraken_request(url_path, data, api_key, api_sec):  # use for making orders
    headers = {"API-Key": api_key,
               "API-Sign": get_kraken_signature(url_path, data, api_sec)}
    resp = requests.post((api_url + url_path), headers=headers, data=data)
    return resp
def isInOpenOrder(curCoin):
    open_orders = k.query_private('OpenOrders')
    open_orders = open_orders['result']['open']
    altName = k.query_public('AssetPairs')['result'][curCoin]['altname']
    for o in open_orders:
        if (open_orders[o]['descr']['pair']  == altName):
            return True
    return False




percentageChange = 1.2  # in percentage form
percentageToUse = 80  # in percentage form
flatPriceToUse = 0  # amount of dollars to use, is in dollars, default to 0 to use percentage
count = 0
coinTime = 0.5 #amount of seconds between each query
iterationTime = 5 #amount of seconds between each iteration (while loop)

# secs = 1800 #30 minutes ago
secs = 2700 #45 minutes ago
# secs = 3600 #60 minutes ago
timeInterval = int(time.time()) - secs


coinList = ["APEUSD", "ADAUSD", "MATICUSD", "ATOMUSD", "TRXUSD", "LDOUSD", "ALGOUSD", "MANAUSD", "SANDUSD", "LRCUSD", "SUSHIUSD", "OCEANUSD", "SHIBUSD"]
# coinList = ["APEUSD", "ADAUSD", "MATICUSD", "ATOMUSD", "TRXUSD", "LDOUSD", "ALGOUSD"]
# coinList = ["ADAUSD"]


#get initial open orders and add them to currentOrderIdList
open_orders_list = k.query_private('OpenOrders')
open_orders_list= open_orders_list['result']['open'].keys()
currentOrderIdList = []
for order in open_orders_list:
    currentOrderIdList.append(order)
time.sleep(coinTime)

while (True):

    try:

        print("count: " + str(count))
        count += 1
        


        print("interval: " + str(secs) + " seconds")
        #go through currentOrderList and see if they are all open, if closed, remove it and put into receipt
        print("current order list: " + str(currentOrderIdList))
        for order_Id in currentOrderIdList:
            order_status = kraken_request("/0/private/QueryOrders", {
                    "nonce": str(int(1000 * time.time())),
                    "txid": order_Id
                }, api_key, private_key).json()['result']
            currentStatus = order_status[order_Id]['status']

            if(currentStatus == 'closed'):
                closedCoin = order_status[order_Id]['descr']['pair']
                # print( order_Id + " is : "  + str(currentStatus))
                message = "SOLD : " + closedCoin
                print(colored(message, 'green'))
                currentOrderIdList.remove(order_Id)
                with open('receipt.txt', 'a') as f:
                    f.write(message + "\n")
                    f.close()
        
        


        for pair in coinList:
            time.sleep(coinTime)#-------------------------------
            print()
            #Current Balance
            balance = kraken_request("/0/private/Balance", {
                "nonce": str(int(1000 * time.time()))
            }, api_key, private_key).json()
            balance = balance['result'] 
            time.sleep(coinTime)#-------------------------------
        
            # amount able to use based off of percentage value indicated at the top
            amountOfCash = float(balance['ZUSD'])
            useAmount = amountOfCash * \
                (percentageToUse * 0.01)  
            
            #volume minimum need to buy in order to sucessfully buy
            orderMin = k.query_public('AssetPairs', {'pair': pair})
            decimalPlaces = orderMin['result'][pair]['pair_decimals']
            orderMin = orderMin['result'][pair]['ordermin'] 
            # print(decimalPlaces)
            time.sleep(coinTime)#-------------------------------
        


            # Get the last 30 minutes worth of OHLC data
            

            past = k.query_public('Trades', {'pair': pair, 'since': timeInterval})
            past_price =float( past['result'][pair][0][0])
            # print("pastPrice: " + str(past_price))
            time.sleep(coinTime)#-------------------------------

            current_price = float(k.query_public('Ticker', {'pair': pair})['result'][pair]['c'][0])
            # print("currentPrice: " + str(current_price))
            sell_price = round(float(current_price + (past_price - current_price)/3), decimalPlaces) #sell_price percentage: currently is 1/3 the percentage change (mean calculation)
            time.sleep(coinTime)#-------------------------------

            #get price change, percentage, 2 decimal places
            price_change = (current_price - past_price) / past_price * 100
            price_change = round(price_change, 2)

        
            #amount of coin volume able to buy 
            amountOfVolume = 0
            amountOfVolume = useAmount/current_price


            # if(flatPriceToUse == 0 ):
            #     amountOfVolume = useAmount/current_price
            # else :
            #     amountOfVolume = flatPriceToUse/current_price
            


            #print lines to help debug, if statements are still needed to function correctly
            # print("USD BALANCE: $" + str(amountOfCash))
            # print("Use Amount (" + str(percentageToUse) + "%) : $" + str(useAmount) + " -> "+ str(amountOfVolume) + " coins")
            # print("ordermin: " + str(orderMin))


            print(colored(pair + " (USD AVAILABLE: $" + str(useAmount) + ")",'light_magenta'))
            print(colored (str(past_price) + " --> " + str(current_price) + "   (" + str(price_change) + "%)", 'cyan'))
            if(isInOpenOrder(pair)):
                print(colored ("is already in open order", 'yellow'))
                continue
            
            if float(amountOfVolume) < float(orderMin):
                print(colored('ordermin limit (have:' + str(amountOfVolume) + ') (need:' + str(orderMin) + ')=======================', 'yellow'))
                continue
            
            

            # if price change is large enough, do a market buy, and limit sell with price sell_price 
            if price_change < -percentageChange:
                # print("openPrice: " + str(past_price))
                # print("closePrice: " + str(current_price))
                # print((ohlc['result'][pair]))
                print(
                    colored("The price of " + pair + " has dropped by more than " + str(percentageChange) + "% in the last 30 minutes  MAKE ORDER", 'light_green'))
                buyOrder = kraken_request("/0/private/AddOrder", {
                    "nonce": str(int(1000 * time.time())),
                    "ordertype": "market",
                    "type": "buy",
                    "volume" : amountOfVolume,
                    "pair": pair,
                }, api_key, private_key)
                print(colored(buyOrder.json(), 'light_green'))
                time.sleep(coinTime)#-------------------------------

                sellOrder = kraken_request("/0/private/AddOrder", {
                    "nonce": str(int(1000 * time.time())),
                    "ordertype": "limit",
                    "type": "sell",
                    "volume" : amountOfVolume,
                    "pair": pair,
                    "price": sell_price,
                }, api_key, private_key)
                print(colored(sellOrder.json(), 'light_green'))
                currentOrderIdList.append(sellOrder.json()['result']['txid'][0])
                time.sleep(coinTime)#-------------------------------

            #    message describing buy and sell process, spits out info into receipt.txt
                message = str(datetime.datetime.now()) + "\t(BOUGHT " + str(useAmount) + " " + pair + " for " + "$" + str(round(current_price,2)) + ")  (SELL AT $" + str(sell_price) + ")" + "  (BALANCE  Before: $" + str(amountOfCash) + " Now: $" + str(amountOfCash - useAmount) + ")"
                print(colored (message, 'light_green'))
                with open('receipt.txt', 'a') as f:
                    f.write(message + "\n")
                f.close()
            else:
                print(colored ("The price of " + str(pair) + " has not dropped by more than " + str(percentageChange) + "% in the chosen interval", 'yellow'))
            

        print(balance)
        print(colored("-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*",'blue'))
         # pasting for now as 15
    except Exception as e: 
        lineError = traceback.extract_tb(e.__traceback__)[-1][1]
        print( colored ("error on line " + str(lineError) + ": " + str(e), 'red'))
        message = str(datetime.datetime.now()) + "\t(ERROR on line " + str(lineError) + " and count " + str(count) + ") :" + str(e)
        with open('receipt.txt', 'a') as f:
            f.write(message + "\n")
            f.close()
        time.sleep(iterationTime)

    time.sleep(iterationTime) 
