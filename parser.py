from bs4 import BeautifulSoup
import urllib.request
import re
import logging
from random import choice
import pickle


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

            for text in author_soup.find_all('div', {"class": "poetry"}):
                haiku = '{}:\n{}\n\n'.format(author_name, text.find('div', {"class": "poetry_title"}).get_text())
                haiku_text = author_soup.find('div', {"class": "block_padding"}).get_text()
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


bot_data = HaikuData()
with open("model.txt", 'wb') as outFile:
    pickle.dump(bot_data, outFile)
