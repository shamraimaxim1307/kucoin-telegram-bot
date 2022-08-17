import sys
import time
from os import getenv

from kucoin.client import Market
from kucoin.client import Trade
from additional.balance.balance import get_valid_currencies
from additional.database.models import User, Api
from additional.secretdata.secretdata import Data
import telebot
# If you want to interact with bot edit data in parentheses, my API data is hidden by .gitignore
# and don't forget change data in kucointelegrambot.py too
bot = telebot.TeleBot(Data.api_tg_key)


class CurrencyData:
    def __init__(self, user_id, symbol_to_roll, symbol_income_percent, symbol_stop):
        self.user_id = user_id
        self.symbol_to_roll = symbol_to_roll + '-USDT'
        self.symbol_income_percent = symbol_income_percent
        self.symbol_stop = symbol_stop

    def connect_kucoin_market(self):
        user = User.get(User.chat_id == self.user_id)
        api = Api.get(Api.foreign_key == user)
        client = Market(api.api_key, api.api_secret, api.api_passphrase)
        return client

    def connect_kucoin_trade(self):
        user = User.get(User.chat_id == self.user_id)
        api = Api.get(Api.foreign_key == user)
        client = Trade(api.api_key, api.api_secret, api.api_passphrase)
        return client

    def check_price(self):
        """
        :return: price of symbol
        :type: str
        """
        client = self.connect_kucoin_market()
        price = client.get_ticker(self.symbol_to_roll)['price']
        return price

    def sell_template(self):
        """
        Sell template for avoiding duplicates
        :return: that's nothing to return, because it's template for another function
        """
        client = self.connect_kucoin_trade()
        symbol_to_roll_balance = get_valid_currencies()[self.symbol_to_roll.replace('-USDT', '')]
        symbol_price = float(self.check_price())
        symbol_decimal = str(symbol_price)[::-1].find('.')
        symbol_price_stop = round(symbol_price - symbol_price * self.symbol_stop, symbol_decimal)
        symbol_price_buy = round((symbol_price + symbol_price * self.symbol_income_percent), symbol_decimal)
        order_sell_id = client.create_limit_order(self.symbol_to_roll, 'sell', symbol_to_roll_balance,
                                                  symbol_price_buy)['orderId']
        bot.send_message(self.user_id,
                         f"Stop is worked or {order_sell_id} is ordered of sale by"
                         f" {round(symbol_price + symbol_price * self.symbol_income_percent, symbol_decimal)}")
        print(f"Stop is worked or {order_sell_id} is ordered of sale by"
              f" {round(symbol_price + symbol_price * self.symbol_income_percent, symbol_decimal)}")
        self.sell_currency(order_sell_id, symbol_price_stop)

    def buy_template(self):
        """
        :return: that's nothing to return, because it's template for another function
        """
        client = self.connect_kucoin_trade()
        symbol_to_roll_balance = get_valid_currencies()[self.symbol_to_roll.replace('-USDT', '')]
        symbol_price = float(self.check_price())
        symbol_decimal = str(symbol_price)[::-1].find('.')
        symbol_price_stop = round(symbol_price + symbol_price * self.symbol_stop, symbol_decimal)
        symbol_price_sell = round((symbol_price - symbol_price * self.symbol_income_percent), symbol_decimal)
        order_buy_id = client.create_limit_order(self.symbol_to_roll, 'buy', symbol_to_roll_balance,
                                                 symbol_price_sell)['orderId']
        bot.send_message(self.user_id,
                         f"Stop is worked or {order_buy_id} is ordered of purchase by {symbol_price_sell}")

        self.buy_currency(order_buy_id, symbol_price_stop)

    def buy_currency(self, order_id, symbol_price_stop):
        """
            This function buys currency and check if stops/cancel is triggered
            :param symbol_price_stop: symbol price for re-create order
            :param order_id: Order ID was given by buy template
            :return: that's function nothing to return
            """
        client_market = self.connect_kucoin_market()
        client_trade = self.connect_kucoin_trade()
        market_price = float(client_market.get_ticker(self.symbol_to_roll)['price'])
        try:
            while True:
                order_buy_id = client_trade.get_order_details(order_id)
                isOrderCancel = order_buy_id['cancelExist']
                isOrderActive = order_buy_id['isActive']
                if isOrderCancel is True:
                    bot.send_message(self.user_id, '❌ALARM:ORDER IS CANCELLED❌')
                    break
                else:
                    if market_price <= symbol_price_stop:
                        bot.send_message(self.user_id, '❌ALARM:ORDER IS TRIGGERED❌')
                        self.buy_template()
                    if isOrderActive is False:
                        bot.send_message(self.user_id, '✅ALARM: CURRENCY IS BOUGHT/SOLD✅')
                        self.sell_template()
                time.sleep(1.500)
        except Exception as e:
            bot.send_message(self.user_id, '❌ALARM:ERROR OCCURRED❌')
            sys.exit(e)

    def sell_currency(self, order_id, symbol_price_stop):
        """
        This function sells currency and check if stops/cancel is triggered
        :param symbol_price_stop: symbol price for re-create order
        :param order_id: Order ID was given by buy template
        :return: that's function nothing to return
        """
        client_market = self.connect_kucoin_market()
        client_trade = self.connect_kucoin_trade()
        market_price = float(client_market.get_ticker(self.symbol_to_roll)['price'])
        try:
            while True:
                order_sell_id = client_trade.get_order_details(order_id)
                isOrderCancel = order_sell_id['cancelExist']
                isOrderActive = order_sell_id['isActive']
                if isOrderCancel is True:
                    bot.send_message(self.user_id, '❌ALARM:ORDER IS CANCELLED❌')
                    break
                else:
                    if market_price <= symbol_price_stop:
                        bot.send_message(self.user_id, '❌ALARM:ORDER IS TRIGGERED❌')
                        self.sell_template()
                    if isOrderActive is False:
                        bot.send_message(self.user_id, '✅ALARM: CURRENCY IS BOUGHT/SOLD✅')
                        self.buy_template()
                time.sleep(1.500)
        except Exception as e:
            bot.send_message(self.user_id, '❌ALARM:ERROR OCCURRED❌')
            sys.exit(e)

    def cancel_orders(self):
        client = self.connect_kucoin_trade()
        client.cancel_all_orders()
        bot.send_message(self.user_id, 'Orders are cancelled. Rolling is stopped')

    def launch_bot(self):
        """
        This function launch currency bot
        :return: that's function nothing to return
        """
        client = self.connect_kucoin_trade()
        client.cancel_all_orders()
        symbol_to_roll_balance = get_valid_currencies()[self.symbol_to_roll.replace('-USDT', '')]
        symbol_price = float(self.check_price())
        symbol_decimal = str(symbol_price)[::-1].find('.')
        symbol_price_sell = round(symbol_price + symbol_price * self.symbol_income_percent, symbol_decimal)
        order_sell_id = client.create_limit_order(self.symbol_to_roll, 'sell', symbol_to_roll_balance,
                                                  symbol_price_sell)['orderId']
        symbol_price_stop = round(symbol_price - symbol_price * self.symbol_stop, symbol_decimal)
        bot.send_message(self.user_id, f'Start rolling...\n{order_sell_id} is ordered for sale by {symbol_price_sell}')
        self.sell_currency(order_sell_id, symbol_price_stop)
