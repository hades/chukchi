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

from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, abort, g, session
from sqlalchemy.orm import scoped_session

from .restutils import setup_rest_app
from ..config import config
from ..db import Session
from ..db.models import User
from ..utils import now

app = Flask(__name__)
app.config.from_object(config)
app.config.from_envvar('CHUKCHI_FLASK_CONFIG', silent=True)

setup_rest_app(app)

db = scoped_session(Session)

LOG = logging.getLogger(__name__)

@app.teardown_request
def shutdown_session(exception=None):
    db.remove()

def needs_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = db.query(User).filter_by(id=session['user']).first() \
                if 'user' in session else None
        if not user:
            abort(401)
        g.user = user
        return f(*args, **kwargs)
    return wrapper

from . import endpoints

# vi: sw=4:ts=4:et
