# This file is part of Chukchi, the free web-based RSS aggregator
#
#   Copyright (C) 2013 Edward Toroshchin <chukchi-project@hades.name>
#
# Chukchi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Chukchi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# Please see the file COPYING in the root directory of this project.
# If you are unable to locate this file, see <http://www.gnu.org/licenses/>.

from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import aliased, deferred, relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import BigInteger, Binary, Boolean, DateTime, Enum, Integer, String, Text

Base = declarative_base()

MAX_CONTENT_TYPE_LEN = 64
MAX_EMAIL_LEN = 120
MAX_ENTRYTITLE_LEN = 255
MAX_ETAG_MODIFIED_LEN = 64
MAX_FEEDNAME_LEN = 255
MAX_OPENID_ASSOC_TYPE_LEN = 64
MAX_OPENID_HANDLE_LEN = 255
MAX_OPENID_SALT_LEN = 40
MAX_OPENID_SERVER_URL_LEN = 2047
MAX_USERNAME_LEN = 80
MAX_URL_LEN = 255

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(MAX_EMAIL_LEN))
    first_login = Column(DateTime(timezone=True), default=datetime.now)
    last_login = Column(DateTime(timezone=True))
    name = Column(String(MAX_USERNAME_LEN), nullable=False, default="")
    openid = Column(String(MAX_URL_LEN))

    def __repr__(self):
        return '<User {}>'.format(self.id)

class Feed(Base):
    __tablename__ = 'feed'

    id = Column(Integer, primary_key=True)
    title = Column(String(MAX_FEEDNAME_LEN), nullable=False)
    subtitle = Column(String(MAX_FEEDNAME_LEN), nullable=False)
    link = Column(String(MAX_URL_LEN), nullable=False)
    feed_url = Column(Text, nullable=False)
    http_etag = Column(String(MAX_ETAG_MODIFIED_LEN))
    http_modified = Column(String(MAX_ETAG_MODIFIED_LEN))
    added = Column(DateTime(timezone=True), default=datetime.now)
    last_update = Column(DateTime(timezone=True))
    json = deferred(Column(Text, nullable=False))
    active = Column(Boolean, nullable=False, default=True)
    retrieved_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)

    def __repr__(self):
        return '<Feed {}>'.format(self.id)

    def __unicode__(self):
        return u"Feed {}".format(self.name)

    def to_json(self):
        return {'id': self.id,
                'title': self.title,
                'subtitle': self.subtitle,
                'link': self.link,
                'feed_url': self.feed_url,
                'last_update': self.last_update,
        }

class Entry(Base):
    __tablename__ = 'entry'

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey(Feed.id), nullable=False)
    guid = Column(String(MAX_URL_LEN))
    link = Column(String(MAX_URL_LEN))
    title = Column(String(MAX_ENTRYTITLE_LEN), nullable=False, default="")
    published = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    retrieved_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    json = deferred(Column(Text, nullable=False, default=""))

    feed = relationship(Feed, backref='entries')

    def to_json(self):
        return {'id': self.id,
                'feed': self.feed.to_json(),
                'guid': self.guid,
                'link': self.link,
                'title': self.title,
                'published': self.published,
                'updated': self.updated,
                'content': [c.to_json() for c in self.content],
        }

class Content(Base):
    __tablename__ = 'content'

    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey(Entry.id), nullable=False)
    type = Column(String(MAX_CONTENT_TYPE_LEN), nullable=False)
    hash = Column(String(40), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    expired = Column(Boolean, nullable=False, default=False)
    summary = Column(Boolean, nullable=False, default=False)
    data = deferred(Column(Text, nullable=False, default=""))

    entry = relationship(Entry, backref='content')

    def to_json(self):
        return {'id': self.id,
                'type': self.type,
                'hash': self.hash,
                'expired': self.expired,
                'summary': self.summary,
                'length': len(self.data),
        }

class Subscription(Base):
    __tablename__ = 'subscription'

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey(Feed.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    feed = relationship(Feed, backref='subscriptions')
    user = relationship(User, backref='subscriptions')

    def to_json(self):
        return {'id': self.id,
                'feed': self.feed.to_json(),
        }

class Unread(Base):
    __tablename__ = 'unread'

    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey(Entry.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    entry = relationship(Entry, backref='unread')
    user = relationship(User, backref='unread')

class OpenIDAssociation(Base):
    __tablename__ = 'openid_association'

    id = Column(Integer, primary_key=True)
    server_url = Column(String(MAX_OPENID_SERVER_URL_LEN), nullable=False)
    handle = Column(String(MAX_OPENID_HANDLE_LEN), nullable=False)
    secret = Column(Binary, nullable=False)
    issued = Column(Integer, nullable=False)
    lifetime = Column(Integer, nullable=False)
    assoc_type = Column(String(MAX_OPENID_ASSOC_TYPE_LEN), nullable=False)

    def copy_assoc(self, assoc):
        self.handle = assoc.handle[:MAX_OPENID_HANDLE_LEN]
        self.secret = assoc.secret
        self.issued = assoc.issued
        self.lifetime = assoc.lifetime
        self.assoc_type = assoc.assoc_type[:MAX_OPENID_ASSOC_TYPE_LEN]

class OpenIDNonce(Base):
    __tablename__ = 'openid_nonce'

    id = Column(Integer, primary_key=True)
    server_url = Column(String(MAX_OPENID_SERVER_URL_LEN), nullable=False)
    timestamp = Column(Integer, nullable=False)
    salt = Column(String(MAX_OPENID_SALT_LEN), nullable=False)

# vi: sw=4:ts=4:et
