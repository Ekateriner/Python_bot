from bs4 import BeautifulSoup
import urllib.request
import re
import logging
from random import choice, choices
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_


engine = create_engine('sqlite:///haiku.db', echo=True)
Base = declarative_base()


class Authors(Base):
    __tablename__ = 'authors_table'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Boolean) #true=japan, false=other
    haiku = relationship("Haiku")


class Haiku(Base):
    __tablename__ = 'haiku_table'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    author_id = Column(Integer, ForeignKey('authors_table.id'))
    author = relationship("Authors", back_populates="haiku")
    words = relationship("Words")


class Words(Base):
    __tablename__ = 'words_table'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    haiku_id = Column(Integer, ForeignKey('haiku_table.id'))
    haiku = relationship("Haiku", back_populates="words")


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


'''telegram part'''
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WrongTextError(ValueError):
    """raise this when it is wrong text in bot"""


class NotFindError(KeyError):
    """raise this when word is not in any haiku"""


def main():
    with open("token.txt", "r") as f:
        this_token = f.readline()
    updater = Updater(token=this_token[:-1])
    '''request_kwargs={'proxy_url': 'socks5://194.182.70.150:1080/'}'''
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    help_handler = CommandHandler('help', bot_help)
    dispatcher.add_handler(help_handler)
    random_handler = CommandHandler('random', bot_random)
    dispatcher.add_handler(random_handler)
    authors_handler = CommandHandler('authors', authors)
    dispatcher.add_handler(authors_handler)
    all_handler = CommandHandler('all', bot_all)
    dispatcher.add_handler(all_handler)
    japan_handler = CommandHandler('japan', japan)
    dispatcher.add_handler(japan_handler)
    other_handler = CommandHandler('other', other)
    dispatcher.add_handler(other_handler)
    haiku_handler = MessageHandler(Filters.text, get_haiku)
    dispatcher.add_handler(haiku_handler)
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()

    updater.idle()


def bot_all(bot, update):
    message = update.message.text
    message = message[5:]
    haiku_list = session.query(Haiku.text).join(Words, Words.haiku_id==Haiku.id).filter(Words.text==message).all()
    if len(haiku_list) != 0:
        random_haiku = choice(haiku_list)[0]
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Sorry we do not find haiku with this word. Please, try again')
        return False

    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)


def japan(bot, update):
    message = update.message.text
    message = message[7:]
    haiku_list = session.query(Haiku.text).join(Words, Words.haiku_id==Haiku.id).join(Authors, Authors.id==Haiku.author_id).filter(and_(Words.text==message, Authors.type==True)).all()
    if len(haiku_list) != 0:
        random_haiku = choice(haiku_list)[0]
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Sorry we do not find haiku with this word. Please, try again')
        return False

    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)


def other(bot, update):
    message = update.message.text
    message = message[7:]
    haiku_list = session.query(Haiku.text).join(Words, Words.haiku_id==Haiku.id).join(Authors, Authors.id==Haiku.author_id).filter(and_(Words.text==message, Authors.type==False)).all()

    if len(haiku_list) != 0:
        random_haiku = choice(haiku_list)[0]
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Sorry we do not find haiku with this word. Please, try again')
        return False

    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)



def get_haiku(bot, update):
    message = update.message.text
    author_haiku = session.query(Haiku.text).join(Authors, Authors.id==Haiku.author_id).filter(Authors.name==message).all()
    if len(author_haiku) != 0:
        random_haiku = choice(author_haiku)[0]
    else:
        bot.send_message(chat_id=update.message.chat_id, text='We don\'t find author with this name')
        return False

    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm a bot, who find haiku for you. "
                          "Please, write keyword or author to start")


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def bot_help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Please, write command and some keyword or just author name to find haiku \n"
                          "commang: \nall - find in all haiku\njapan - find only in japan haiku"
                          "\nother - find in other author(ordinary people)\n"
                          "Example /all Сакура\n\n"
                          "Also you can use:\n/random - find random haiku(without keywords)\n"
                          "/authors - to get list with authors name\n\n"
                          "P.S. Attention: all haiku on russian language, consequently, keywords too")


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def bot_random(bot, update):
    all_haiku = session.query(Haiku.text).all()
    random_haiku = choice(all_haiku)[0]
    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)


def authors(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='some japan authors:')
    random_authors = session.query(Authors.name).filter(Authors.type==True).all()
    for author in choices(random_authors, k=5):
        bot.send_message(chat_id=update.message.chat_id, text=author[0])
    
    bot.send_message(chat_id=update.message.chat_id, text='some other authors:')
    random_authors = session.query(Authors.name).filter(Authors.type==False).all()
    for author in choices(random_authors, k=5):
        bot.send_message(chat_id=update.message.chat_id, text=author[0])


print("I'm ready")
main()
