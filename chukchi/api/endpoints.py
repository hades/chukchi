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

import logging

from flask import abort, g, request, session

from . import app, db, needs_session
from ..db.models import User

LOG = logging.getLogger(__name__)

@app.errorhandler(KeyError)
def no_key(e):
    return {'error': 400,
            'message': 'A field was missing from the request'}, 400

@app.route('/session', methods=('POST',))
def post_session():
    user = db.query(User).first()
    if not user:
        user = User(email='', name='user')
        db.add(user)
        db.flush()
        db.commit()
    session['user'] = user.id # TODO implement auth
    return {}

@app.route('/session', methods=('GET', 'DELETE'))
@needs_session
def get_delete_session():
    if request.method == 'DELETE':
        session.clear()
        return {}
    return {'user': g.user.id}

# vi: sw=4:ts=4:et
