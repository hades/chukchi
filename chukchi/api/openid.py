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

from __future__ import absolute_import

from time import time

from openid.association import Association
from openid.store.interface import OpenIDStore
from openid.store.nonce import SKEW

from flask import g, redirect, request, session
from flask.ext.openid import OpenID

from . import app, db

from ..db.models import OpenIDAssociation, OpenIDNonce, User
from ..db.models import MAX_OPENID_SALT_LEN, MAX_OPENID_SERVER_URL_LEN, MAX_USERNAME_LEN

class SQLAlchemyStore(OpenIDStore):
    def __init__(self, db):
        self.db = db

    def _get(self, server_url, handle=None):
        query = self.db.query(OpenIDAssociation).filter_by(server_url=server_url[:MAX_OPENID_SERVER_URL_LEN])
        if handle:
            query = query.filter_by(handle=handle)
        return query.order_by(OpenIDAssociation.id.desc()).first()

    def storeAssociation(self, server_url, association):
        assoc = self._get(server_url, association.handle)
        if not assoc:
            assoc = OpenIDAssociation(server_url=server_url[:MAX_OPENID_SERVER_URL_LEN])
        assoc.copy_assoc(association)
        db.add(assoc)
        db.commit()

    def getAssociation(self, server_url, handle=None):
        assoc = self._get(server_url, handle)
        if assoc:
            return Association(handle=assoc.handle,
                               secret=assoc.secret,
                               issued=assoc.issued,
                               lifetime=assoc.lifetime,
                               assoc_type=assoc.assoc_type)

    def removeAssociation(self, server_url, handle):
        assoc = self._get(server_url, handle)
        if assoc:
            db.delete(assoc)
            db.commit()
            return True
        return False

    def useNonce(self, server_url, timestamp, salt):
        if abs(timestamp - time()) > SKEW:
            return False

        nonce = db.query(OpenIDNonce).filter_by(server_url=server_url[:MAX_OPENID_SERVER_URL_LEN],
                                                timestamp=timestamp,
                                                salt=salt[:MAX_OPENID_SALT_LEN])\
                                     .first()
        if nonce:
            return False
        db.add(OpenIDNonce(server_url=server_url[:MAX_OPENID_SERVER_URL_LEN],
                           timestamp=timestamp,
                           salt=salt[:MAX_OPENID_SALT_LEN]))
        db.commit()
        return True

    def cleanupNonce(self):
        db.query(OpenIDNonce).filter(OpenIDNonce.timestamp < (int(time()) - SKEW)).delete()
        db.commit()

    def cleanupAssociations(self):
        db.query(OpenIDAssociation).filter(OpenIDAssociation.issued + OpenIDAssociation.lifetime > int(time()))\
                                   .delete()
        db.commit()

openid = OpenID(app, store_factory=lambda: SQLAlchemyStore(db))

@app.route('/openid/login', methods=('GET', 'POST'))
@openid.loginhandler
def login():
    if app.debug and app.config.get('DEBUG_OVERRIDE_USER'):
        g.user = db.query(User).filter_by(id=app.config.get('DEBUG_OVERRIDE_USER')).first()
        if g.user: session['openid'] = g.user.openid
    if g.user is not None:
        return redirect('/')
    if request.method == 'POST':
        identity = request.form.get('openid')
        if identity:
            return openid.try_login(identity, ask_for=('nickname', 'email'))
    session['openid_error'] = openid.fetch_error()
    return redirect('/')

@openid.after_login
def makeuser(response):
    session['openid'] = response.identity_url
    user = db.query(User).filter_by(openid=response.identity_url).first()
    if not user:
        user = User(openid=response.identity_url,
                    email=getattr(response, 'email', ''),
                    name=(getattr(response, 'nickname', '') or response.identity_url)[:MAX_USERNAME_LEN])
        db.add(user)
        db.commit()
    g.user = user
    return redirect('/')

# vi: sw=4:ts=4:et
