from peewee import SqliteDatabase, Model, CharField, ForeignKeyField

db = SqliteDatabase(r'/home/shamraimaxim/Стільниця/kucoinproject/kucoin-api-seller('
                    r'telegrambot)/additional/database/api.db')


class User(Model):
    chat_id = CharField()

    class Meta:
        database = db


class Api(Model):
    api_key = CharField()
    api_secret = CharField()
    api_passphrase = CharField()
    foreign_key = ForeignKeyField(User)

    class Meta:
        database = db


if __name__ == '__main__':
    db.create_tables([Api, User])
