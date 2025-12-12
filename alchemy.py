from typing import List, Text
from typing import Optional

import fuzzysearch

from sqlalchemy import (create_engine, insert, select,
                        Column, Table, String, Integer, ForeignKey,
                        TIMESTAMP, TEXT, DATE, DATETIME) # importing sqlalchemy datatypes
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import relationship, mapped_column, DeclarativeBase, Mapped, Session

with open('./dbid') as f:
    username = f.readline().replace(' ', '%40')
    password = f.readline().replace(' ', '%40')

engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@camorka.ru:3306/issa')
session = Session(bind=engine)

class Base(DeclarativeBase):
    pass

ratingstoisbn = Table(
    'ratingstoisbn',
    Base.metadata,
    Column('id', primary_key = True),
    Column('rating', ForeignKey('ratings.rating')),
    Column('user_id', ForeignKey('users.id')),
)

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    created_at = mapped_column(TIMESTAMP)

class Rating(Base):
    __tablename__ = 'ratings'

    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[float] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    isbn: Mapped[int] = mapped_column(ForeignKey('books.id'))
    body = mapped_column(TEXT)
    rated_at = mapped_column(TIMESTAMP)

class Book(Base):
    __tablename__ = 'books'
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    title: Mapped[str]
    isbn: Mapped[int] = mapped_column(ForeignKey('isbn.id'))
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.id'))
    location_id: Mapped[int] = mapped_column(ForeignKey('location.id'))
    status: Mapped[str] = mapped_column(ForeignKey('users.id'))
    created_at = mapped_column(TIMESTAMP)
    last_used = mapped_column(TIMESTAMP)
    embedding: Mapped[int] = mapped_column(ForeignKey('embeddings.id'))

    author = relationship('Author')
    location = relationship('Location')
    isbn_rel = relationship('ISBN')

    def ldist(self, string):
        fuzzysearch.ldist(self.title, string) + fuzzysearch.ldist(self.author.full_name, string)

class ISBN(Base):
    __tablename__ = 'isbn'
    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[int] = mapped_column(ForeignKey('embeddings.id'))

class Checkout(Base):
    __tablename__ = 'checkouts'

    id: Mapped[int] = mapped_column(primary_key=True)
    book: Mapped[int] = mapped_column(ForeignKey('books.id'))
    checkout_at = mapped_column(TIMESTAMP)

class Embedding(Base):
    __tablename__ = 'embeddings'

    id: Mapped[int] = mapped_column(primary_key=True)
    params: Mapped[int]
    published_at = mapped_column(DATE)

class Author(Base):
    __tablename__ = 'authors'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    rating: Mapped[float]

class Location(Base):
    __tablename__ = 'location'

    id: Mapped[int] = mapped_column(primary_key=True)
    common_name: Mapped[str]
    building_id: Mapped[int] = mapped_column(ForeignKey('buildings.id'))
    shelf: Mapped[int]
    storey: Mapped[int]

class Building(Base):
    __tablename__ = 'buildings'

    id: Mapped[int] = mapped_column(primary_key=True)
    common_name: Mapped[str]