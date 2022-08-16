import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from additional.database.models import User, Api
import aiogram.utils.markdown as fmt

bot = Bot('5731092165:AAF5lI0EkPKtXzaRAmJ4QTIq20Trb4Ga02I')

dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)


class ApiData(StatesGroup):
    api_key = State()
    api_secret = State()
    api_passphrase = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = ['📈 | Start rolling currency', '🔑 | Set API Data', '⚙️ | Change API Data',
               '❓ | How to create an API on KuCoin']
    keyboard.add(*buttons)
    if User.select().where(User.chat_id == message.chat.id):
        await message.reply(f'Hello, {fmt.hbold(message.chat.first_name)} {fmt.hbold(message.chat.last_name)}',
                            parse_mode=types.ParseMode.HTML
                            , reply_markup=keyboard)
    else:
        User.create(
            chat_id=message.chat.id,
        )
        await message.reply(f'Hello, {fmt.hbold(message.chat.first_name)} {fmt.hbold(message.chat.last_name)}',
                            parse_mode=types.ParseMode.HTML
                            , reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == '📈 | Start rolling currency')
async def bot_answer(message: types.Message):
    user = User.get(User.chat_id == message.chat.id)
    if Api.select().where(Api.foreign_key == user):
        await message.answer('ok')
    else:
        await message.reply('ERROR: API not set. Choose "Set API Data" button')


@dp.message_handler(lambda message: message.text == '🔑 | Set API Data')
async def bot_answer(message: types.Message):
    user = User.get(User.chat_id == message.chat.id)
    if Api.select().where(Api.foreign_key == user):
        await message.answer('API is set. Choose "Change API Data" button to change data')
    else:
        await ApiData.api_key.set()

        await message.reply('If you want cancel action enter "/cancel"\n'
                            'Enter your API key: ')


@dp.message_handler(state='*', commands='cancel')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.set_state()
    if current_state is None:
        return
    logging.info(f'Cancelling state {current_state}')
    await message.reply('Cancelled!')
    await state.finish()


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


@dp.message_handler(lambda message: message.text == '❓ | How to create an API on KuCoin')
async def bot_answer(message: types.Message):
    link = 'https://www.kucoin.com/support/360015102174-How-to-Create-an-API#:~:text=Go%20to%20KuCoin.com%2C%20and,' \
           'the%20function%20and%20IP%20restrictions '
    await message.reply(f'{fmt.hide_link(link)}This site can help you with your issue\n'
                        f'{fmt.hlink("CLICK HERE", link)}', parse_mode=types.ParseMode.HTML)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
