from peewee import SqliteDatabase, Model, CharField, ForeignKeyField
from additional.secretdata.secretdata import Data

# If you want to create a database, change path in parentheses,
# because I hide my path data into secretdata, that also hidden by .gitignore
db = SqliteDatabase(Data.my_path)


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
