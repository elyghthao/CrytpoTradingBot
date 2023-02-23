# CrytpoTradingBot
Crypto Trading Bot designed to buy in percentages on dips greater than chosen percentage (default is 1.5%) and place instant limit orders with price increased by 33% (subject to change) of price change. Strategy is to catch the small dips and have small profits over a very short amount of time -> "Death By A Thousand Cuts"  <br>
Uses Python3 and KrakenAPI <br>
Designed to constantly run on RaspberryPi3 to catch the dips in time intervals (defaulted to 30 min intervals)<br>
Has a receipt function that documents when buy orders are made, when sell orders are completed, and when any query request fails<br>

Manipulated Data: 
* Percentage of USD balance used on each buy in
* Percentage to place limit sells on after buying
* Time between each query
* Predicted profit margins
* Chosen coins


 
