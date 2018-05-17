from bs4 import BeautifulSoup
import urllib.request
import re
import logging
from random import choice
import pickle
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


def parser_japan():
    response = urllib.request.urlopen('http://japanpoetry.ru/japan-poets')
    html = response.read()
    html = html.decode('utf-8')

    soup = BeautifulSoup(html, 'lxml')
    japan_authors = soup.find_all('div', {"class": "author_name"})

    japan_haiku = {}
    for author in japan_authors:
        for a_tag in author.find_all('a'):

            author_response = urllib.request.urlopen('http://japanpoetry.ru{}'.format(a_tag['href']))
            author_html = author_response.read()
            author_html = author_html.decode('utf-8')
            author_soup = BeautifulSoup(author_html, 'lxml')

            author_name = (author_soup.find('h1'))['title']
            japan_haiku[author_name] = []
            all_texts = author_soup.find_all('div', {"class": "poetry"})
            for text in all_texts:
                href = ((text.find('div', {"class": "details"})).find('a'))['href']

                text_response = urllib.request.urlopen('http://japanpoetry.ru{}'.format(href))
                text_html = text_response.read()
                text_html = text_html.decode('utf-8')
                text_soup = BeautifulSoup(text_html, 'lxml')

                haiku = '{}:\n{}\n\n'.format(author_name, text_soup.find('h1').get_text())
                haiku_text = text_soup.find('div', {"class": "block_padding"}).get_text()
                haiku = '{}{}'.format(haiku, haiku_text)
                japan_haiku[author_name].append(haiku)
    return japan_haiku


def parser_other():
    response2 = urllib.request.urlopen('http://japanpoetry.ru/authors')
    html2 = response2.read()
    html2 = html2.decode('utf-8')

    soup2 = BeautifulSoup(html2, 'lxml')
    other_authors = soup2.find_all('div', {"class": "author_name"})

    other_haiku = {}
    for author in other_authors:
        for a_tag in author.find_all('a'):

            author_response = urllib.request.urlopen('http://japanpoetry.ru{}'.format(a_tag['href']))
            author_html = author_response.read()
            author_html = author_html.decode('utf-8')
            author_soup = BeautifulSoup(author_html, 'lxml')

            author_name = (author_soup.find('h1'))['title']
            other_haiku[author_name] = []

            for text in author_soup.find_all('div', {"class": "block_pandding"}):
                haiku = '{}:\n{}\n\n'.format(author_name, text.find('div', {"class": "poetry_title"}).get_text())
                haiku_text = author_soup.find('div', {"class": "foreword"}).get_text()
                haiku = '{}{}\n'.format(haiku, haiku_text)
                haiku_text = author_soup.find('div', {"class": "poetry_text"}).get_text()
                haiku = '{}{}'.format(haiku, haiku_text)
                other_haiku[author_name].append(haiku)
    return other_haiku


def dict_creator_japan(japan_haiku):
    japan_key_words = {}
    for author in japan_haiku:
        for i in range(len(japan_haiku[author])):
            haiku = japan_haiku[author][i]
            index = haiku.find(':')
            words = re.split(r'[ |\r|\n]+', haiku[index + 1:])
            for word in words:
                if word in japan_key_words:
                    japan_key_words[word].append((author, i))
                else:
                    japan_key_words[word] = []
                    japan_key_words[word].append((author, i))
    return japan_key_words


def dict_creator_other(other_haiku):
    other_key_words = {}
    for author in other_haiku:
        for i in range(len(other_haiku[author])):
            haiku = other_haiku[author][i]
            index = haiku.find(':')
            words = re.split(r'[ |\r|\n]+', haiku[index + 1:])
            for word in words:
                if word in other_key_words:
                    other_key_words[word].append((author, i))
                else:
                    other_key_words[word] = []
                    other_key_words[word].append((author, i))
    return other_key_words


class HaikuData:
    def __init__(self):
        self.japan_haiku = parser_japan()
        self.other_haiku = parser_other()
        self.japan_key_words = dict_creator_japan(self.japan_haiku)
        self.other_key_words = dict_creator_other(self.other_haiku)

    def update(self):
        self.japan_haiku = {}
        self.other_haiku = {}
        self.japan_key_words = {}
        self.other_key_words = {}
        self.japan_haiku = parser_japan()
        self.other_haiku = parser_other()
        self.japan_key_words = dict_creator_japan(self.japan_haiku)
        self.other_key_words = dict_creator_other(self.other_haiku)


'''telegram part'''
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

'''bot_data = HaikuData()'''
with open("model.txt", 'rb') as file:
    bot_data = pickle.load(file)


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
    haiku_list = []
    if message in bot_data.japan_key_words.keys():
        haiku_pair = bot_data.japan_key_words[message][0]
        haiku_list.append(bot_data.japan_haiku[haiku_pair[0]][haiku_pair[1]])
    if message in bot_data.other_key_words.keys():
        haiku_pair = bot_data.other_key_words[message][0]
        haiku_list.append(bot_data.other_haiku[haiku_pair[0]][haiku_pair[1]])
    
    if len(haiku_list) != 0:
        random_haiku = choice(haiku_list)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Sorry we do not find haiku with this word. Please, try again')
        return False

    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)


def japan(bot, update):
    message = update.message.text
    message = message[7:]
    haiku_list = []
    if message in bot_data.japan_key_words.keys():
        haiku_pair = bot_data.japan_key_words[message][0]
        haiku_list.append(bot_data.japan_haiku[haiku_pair[0]][haiku_pair[1]])  

    if len(haiku_list) != 0:
        random_haiku = choice(haiku_list)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Sorry we do not find haiku with this word. Please, try again')
        return False

    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)


def other(bot, update):
    message = update.message.text
    message = message[7:]
    haiku_list = []
    if message in bot_data.other_key_words.keys():
        haiku_pair = bot_data.other_key_words[message][0]
        haiku_list.append(bot_data.other_haiku[haiku_pair[0]][haiku_pair[1]])

    if len(haiku_list) != 0:
        random_haiku = choice(haiku_list)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Sorry we do not find haiku with this word. Please, try again')
        return False

    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)



def get_haiku(bot, update):
    message = update.message.text
    if message in bot_data.japan_haiku.keys() or message in bot_data.other_haiku.keys():
        if message[0] in bot_data.japan_haiku.keys():
            random_haiku = choice(list(bot_data.japan_haiku[message]))
        else:
            random_haiku = choice(list(bot_data.other_haiku[message]))
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
    flag = choice([True, False])
    if flag:
        author = choice(list(bot_data.japan_haiku.keys()))
        random_haiku = choice(bot_data.japan_haiku[author])
    else:
        author = choice(list(bot_data.other_haiku.keys()))
        random_haiku = choice(bot_data.other_haiku[author])
    bot.send_message(chat_id=update.message.chat_id, text=random_haiku)


def authors(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='japan authors:')
    for author in bot_data.japan_haiku.keys():
        bot.send_message(chat_id=update.message.chat_id, text=author)
    bot.send_message(chat_id=update.message.chat_id, text='other authors:')
    for author in bot_data.other_haiku.keys():
        bot.send_message(chat_id=update.message.chat_id, text=author)


print("I'm ready")
main()
