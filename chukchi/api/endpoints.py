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
from ..config import config
from ..db.models import *
from ..utils import now

LOG = logging.getLogger(__name__)

@app.errorhandler(KeyError)
def no_key(e):
    return {'error': 400,
            'message': 'A field was missing from the request'}, 400

@app.route('/session', methods=('POST',))
def post_session():
    backend = get_backend(request.json['backend'])
    try:
        user, bdata = backend.authenticate(db, request.json['data'])
        session['user'] = user.id
        session['bdata'] = bdata
        session['backend'] = request.json['backend']

        db.commit()
        return {'user': user.id,
                'backend': session['backend'],
                'bdata': bdata}
    except BackendError, e:
        return {'error': 401,
                'message': str(e)}, 401

@app.route('/session', methods=('GET', 'DELETE'))
@needs_session
def get_delete_session():
    if request.method == 'DELETE':
        session.clear()
        return {}
    return {'user': g.user.id,
            'backend': session['backend'],
            'bdata': session.get('bdata', {}),
           }
