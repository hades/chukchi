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
import sys

from datetime import timedelta

from sqlalchemy.orm import scoped_session

from chukchi.config import config
from chukchi.db import Session
from chukchi.db.models import Feed
from chukchi.feed.parse import update_feed
from chukchi.utils import now

logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)

LOG = logging.getLogger(__name__)

db_search = Session()
db_update = scoped_session(Session)

for feed in db_search.query(Feed).filter( Feed.active == True,
                                          Feed.retrieved_at <= (now() - timedelta(**config.UPDATE_DELAY)) ):
    feed_repr = repr(feed)
    try:
        db_search.expunge(feed)
        update_feed(db_update, feed=feed)
        db_update.commit()
    except Exception, e:
        LOG.exception("failure updating feed %s", feed_repr)
    db_update.remove()

# vi: sw=4:ts=4:et
