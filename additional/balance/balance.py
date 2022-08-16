# Example for get balance of accounts in python
from kucoin.client import Market
from kucoin.client import User
from additional.secretdata.secretdata import Data


def get_valid_currencies():
    client = User(Data.api_key, Data.api_secret, Data.api_passphrase)
    symbols = client.get_account_list()
    result_symbols = {}
    for symbol in symbols:
        if symbol['type'] == 'trade':
            result_symbols.update([(f"{symbol['currency']}-USDT", symbol['balance'])])
    client = Market(Data.api_key, Data.api_secret, Data.api_passphrase)
    market_symbols = client.get_symbol_list()
    result_valid_symbols = {}
    for market_symbol in market_symbols:
        if market_symbol['symbol'] in result_symbols:
            if float(market_symbol['baseMinSize']) <= float(result_symbols[market_symbol['symbol']]):
                result_valid_symbols.update([(market_symbol['symbol'].replace('-USDT', ''),
                                              result_symbols[market_symbol['symbol']])])
    return result_valid_symbols


if __name__ == '__main__':
    get_valid_currencies()
