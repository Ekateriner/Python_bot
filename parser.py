from bs4 import BeautifulSoup
import urllib.request
import re
import logging
from random import choice
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker


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


def parser_japan():
    response = urllib.request.urlopen('http://japanpoetry.ru/japan-poets')
    html = response.read()
    html = html.decode('utf-8')

    soup = BeautifulSoup(html, 'lxml')
    japan_authors = soup.find_all('div', {"class": "author_name"})
  
    for author in japan_authors:
        for a_tag in author.find_all('a'):

            author_response = urllib.request.urlopen('http://japanpoetry.ru{}'.format(a_tag['href']))
            author_html = author_response.read()
            author_html = author_html.decode('utf-8')
            author_soup = BeautifulSoup(author_html, 'lxml')

            author_name = (author_soup.find('h1'))['title']
            current_author = Authors(name=author_name, type=True)      
            session.add(current_author)
            session.commit()

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
                current_haiku = Haiku(text=haiku)
                current_author.haiku.append(current_haiku)
                session.add(current_haiku)
                session.commit()


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
            current_author = Authors(name=author_name, type=False)
            session.add(current_author)
            session.commit()

            for text in author_soup.find_all('div', {"class": "block_padding"}):
                haiku = '{}:\n{}\n\n'.format(author_name, text.find('div', {"class": "poetry_title"}).get_text())
                haiku_text = text.find('div', {"class": "foreword"}).get_text()
                haiku = '{}{}\n'.format(haiku, haiku_text)
                haiku_text = text.find('div', {"class": "poetry_text"}).get_text()
                haiku = '{}{}'.format(haiku, haiku_text)
                current_haiku = Haiku(text=haiku)
                current_author.haiku.append(current_haiku)
                session.add(current_haiku)
                session.commit()


def dict_creator():
    for all_haiku in session.query(Haiku).join(Authors, Authors.id==Haiku.author_id):
        a_haiku = all_haiku.text
        index = a_haiku.find('\n\n')
        words = re.split(r'[ |\r|\n]+', a_haiku[index + 2:])
        for word in words:
            current_word = Words(text=word)
            all_haiku.words.append(current_word)
            session.add(current_word)
            session.commit()

            
parser_japan()
parser_other()
dict_creator()
