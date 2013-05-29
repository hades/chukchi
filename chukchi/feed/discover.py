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

from ..db.models import Feed
from .parse import update_feed

LOG = logging.getLogger(__name__)

def discover(db, url):
    feed = db.query(Feed).filter_by(feed_url=url).first()
    if feed: return feed

    feed = update_feed(db, url=url)
    if feed:
        db.add(feed)
        db.flush()
        return feed
    # TODO: discover feeds on HTML pages

    LOG.error("discovery failed for url %s", url)
    return None

# vi: sw=4:ts=4:et
