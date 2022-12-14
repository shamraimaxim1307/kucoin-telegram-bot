# Import logging for log our errors
import logging

# Import aiogram modules for working bot
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import aiogram.utils.markdown as fmt

# Import my local files for working with KuCoin API
from additional.kucoinseller import CurrencyData
from additional.balance.balance import get_valid_currencies
from additional.secretdata.secretdata import Data
from additional.database.models import User, Api

# !!! IMPORTANT !!!
# If you want to interact with bot edit data in parentheses, my API data is hidden by .gitignore
# and don't forget change data in kucoinseller.py too
bot = Bot(Data.api_tg_key)

dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)


# ApiData is created for collecting data from user about KuCoin API
class ApiData(StatesGroup):
    api_key = State()
    api_secret = State()
    api_passphrase = State()


# StateCurrencyData is created for collecting data from user about rolling currency
class StateCurrencyData(StatesGroup):
    symbol_to_roll = State()
    symbol_income_percent = State()
    symbol_stop = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = ['📈 | Start rolling currency', '🔑 | Set API Data', '⚙️ | Change API Data',
               '❓ | How to create an API on KuCoin']
    keyboard.add(*buttons)
    # If the user is in our database we just greet them, otherwise we create the data in the database and greet
    if User.select().where(User.chat_id == message.chat.id):
        await message.reply(f'Hello, {fmt.hbold(message.chat.first_name)} {fmt.hbold(message.chat.last_name)}',
                            parse_mode=types.ParseMode.HTML,
                            reply_markup=keyboard)
    else:
        User.create(
            chat_id=message.chat.id,
        )
        await message.reply(f'Hello, {fmt.hbold(message.chat.first_name)} {fmt.hbold(message.chat.last_name)}',
                            parse_mode=types.ParseMode.HTML,
                            reply_markup=keyboard)


@dp.message_handler(commands='menu')
async def cmd_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = ['📈 | Start rolling currency', '🔑 | Set API Data', '⚙️ | Change API Data',
               '❓ | How to create an API on KuCoin']
    keyboard.add(*buttons)
    await message.reply(f'Hello, {fmt.hbold(message.chat.first_name)} {fmt.hbold(message.chat.last_name)}.\n'
                        f'{fmt.hbold("You are in main menu:")}',
                        parse_mode=types.ParseMode.HTML,
                        reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == '❓ | How to create an API on KuCoin')
async def bot_answer(message: types.Message):
    link = 'https://www.kucoin.com/support/360015102174-How-to-Create-an-API#:~:text=Go%20to%20KuCoin.com%2C%20and,' \
           'the%20function%20and%20IP%20restrictions '
    await message.reply(f'{fmt.hide_link(link)}This site can help you with your issue\n'
                        f'{fmt.hlink("CLICK HERE", link)}', parse_mode=types.ParseMode.HTML)


# TODO: Create command cancel that stop kucoin bot. Coming soon!
# @dp.message_handler(commands='cancel')
# async def cmd_cancel(message: types.Message):
#     instance = CurrencyData(StateCurrencyData.user_id, StateCurrencyData.symbol_to_roll,
#                             StateCurrencyData.symbol_income_percent, StateCurrencyData.symbol_stop)
#     instance.cancel_orders()
#     await message.reply('Cancelled by command!')

# This is a handler created to cancel any operation requested from the user.


@dp.message_handler(lambda message: message.text == '📈 | Start rolling currency')
async def bot_answer(message: types.Message):
    user = User.get(User.chat_id == message.chat.id)
    if Api.select().where(Api.foreign_key == user):
        # We get valid currencies and distribute each to an array cell,
        # then output them on Telegram keyboard
        valid_currencies = get_valid_currencies()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        list_currencies = []
        for key in valid_currencies.keys():
            list_currencies.append(key)
        keyboard.add(*list_currencies)

        await StateCurrencyData.symbol_to_roll.set()

        await message.reply('If you want cancel action enter "/cancel"\n'
                            'Choose valid currency: ', reply_markup=keyboard)
    else:
        await message.reply('ERROR: API not set. Choose "Set API Data" button')


@dp.message_handler(state='*', commands='cancel')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info(f'Cancelling state {current_state}')
    await message.reply('Cancelled!')
    await cmd_menu(message)
    await state.finish()


@dp.message_handler(state=StateCurrencyData.symbol_to_roll)
async def process_symbol_to_roll(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardRemove()
    async with state.proxy() as data:
        data['symbol_to_roll'] = message.text
    await StateCurrencyData.next()

    await message.reply('If you want cancel action enter "/cancel"\n'
                        'Enter incoming percent of price you want to earn:', reply_markup=keyboard)


@dp.message_handler(state=StateCurrencyData.symbol_income_percent)
async def process_symbol_income_percent(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['symbol_income_percent'] = message.text
    if data['symbol_income_percent'].isdigit():
        await StateCurrencyData.next()

        await message.reply('If you want cancel action enter "/cancel"\n'
                            'Enter stop-order percent of price you want to stop order, if it is triggered:')
    else:
        await StateCurrencyData.symbol_income_percent.set()

        await message.reply('ERROR: Invalid incoming percent\n'
                            'Enter incoming percent of price you want to earn:')


@dp.message_handler(state=StateCurrencyData.symbol_stop)
async def process_symbol_stop(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['symbol_stop'] = message.text
    if data['symbol_stop'].isdigit():
        user_id = message.chat.id
        symbol_to_roll = data['symbol_to_roll']
        symbol_income_percent = float(data['symbol_income_percent']) / 100
        symbol_stop = float(data['symbol_stop']) / 100
        await state.finish()

        # Create an instance of CurrencyData and put it in function start_rolling
        instance = CurrencyData(user_id, symbol_to_roll, symbol_income_percent, symbol_stop)
        await start_rolling(message, instance)
    else:
        await StateCurrencyData.symbol_stop.set()

        await message.reply('ERROR: Invalid stop-order percent\n'
                            'Enter stop-order percent of price you want to stop order, if it is triggered:')


async def start_rolling(message: types.Message, instance):
    instance.launch_bot()
    # Output start menu keyboard
    await cmd_menu(message)


@dp.message_handler(lambda message: message.text == '🔑 | Set API Data')
async def bot_answer(message: types.Message):
    user = User.get(User.chat_id == message.chat.id)
    if Api.select().where(Api.foreign_key == user):
        await message.answer('API is set. Choose "Change API Data" button to change data')
    else:
        await ApiData.api_key.set()

        await message.reply('If you want cancel action enter "/cancel"\n'
                            'Enter your API key: ')


@dp.message_handler(state=ApiData.api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_key'] = message.text
    await ApiData.next()
    await message.reply('If you want cancel action enter "/cancel"\n'
                        'Enter your API secret: ')


@dp.message_handler(state=ApiData.api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_secret'] = message.text
    await ApiData.next()
    await message.reply('If you want cancel action enter "/cancel"\n'
                        'Enter your API passphrase: ')


@dp.message_handler(state=ApiData.api_passphrase)
async def process_api_passphrase(message: types.Message, state: FSMContext):
    user = User.get(User.chat_id == message.chat.id)
    async with state.proxy() as data:
        data['api_passphrase'] = message.text
    if Api.select().where(Api.foreign_key == user):
        query = Api.update(api_key=data['api_key'], api_secret=data['api_secret'],
                           api_passphrase=data['api_passphrase']).where(Api.foreign_key == user)
        query.execute()
        await message.answer('Data is updated!')
    else:
        Api.create(
            api_key=data['api_key'],
            api_secret=data['api_secret'],
            api_passphrase=data['api_passphrase'],
            foreign_key=user
        )
        await message.answer('Data is created!')
    await state.finish()


@dp.message_handler(lambda message: message.text == '⚙️ | Change API Data')
async def bot_answer(message: types.Message):
    user = User.get(User.chat_id == message.chat.id)
    if Api.select().where(Api.foreign_key == user):
        await ApiData.api_key.set()

        await message.reply('If you want cancel action enter "/cancel"\n'
                            'Enter your API key: ')
    else:
        await message.reply('Nothing to change!')


@dp.message_handler()
async def bot_answer(message: types.Message):
    await message.reply("I don't understand you!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
