import telebot

bot = telebot.TeleBot('5498227390:AAFThIO_aA233p85O-3Cm4Pctpqrd0PVDNY')

message_id = '963230436'


def recieve_alarm(response):
    if response == '400':
        bot.send_message(message_id, '❌ALARM:ERROR OCCURRED❌')
    elif response == '402':
        bot.send_message(message_id, '❌ALARM:ORDER IS CANCELLED❌')
    elif response == '401':
        bot.send_message(message_id, "❌ALARM:ORDER IS TRIGGERED❌")
    else:
        bot.send_message(message_id, '✅ALARM: CURRENCY IS BOUGHT/SOLD✅')
