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

import hashlib
import logging
import time

import feedparser

from ..db.models import Content, Feed, Entry, Subscription, Unread
from ..db.models import MAX_CONTENT_TYPE_LEN, MAX_ENTRYTITLE_LEN, MAX_FEEDNAME_LEN, MAX_URL_LEN
from ..utils import json_dumps, make_datetime, now

LOG = logging.getLogger(__name__)

def parse_content(c, **kwargs):
    content = Content(**kwargs)
    content.type = c.get('type', 'text/plain')[:MAX_CONTENT_TYPE_LEN]
    content.data = c.get('value', '')
    content.hash = hashlib.sha1(content.data.encode('utf-8')).hexdigest()
    return content

def update_feed(db, feed=None, url=None):
    assert feed or url

    LOG.debug("update_feed: %r %s", feed, url)

    if not feed:
        feed = Feed(feed_url=url)
    pf = feedparser.parse(feed.feed_url, etag=feed.http_etag, modified=feed.http_modified)
    status = pf.get('status', 555)
    LOG.debug("update_feed: status %s", status)
    if status not in (200, 301, 302, 304):
        if status == 410:
            feed.active = False
            db.add(feed)
        LOG.error("update_feed: HTTP error %s on feed url %s", status, feed.feed_url)
        return None

    feed.retrieved_at = now()

    if status == 304: # not modified
        db.add(feed)
        return feed

    if status == 301:
        LOG.info("update_feed: HTTP 301 on feed %r, %s -> %s", feed.id, feed.feed_url, pf.href)
        feed.feed_url = pf.href

    pf_feed = pf.get('feed', None)
    if not pf_feed:
        LOG.error("update_feed: feed is missing from parsed feed %r: %r", feed, pf)
        return None

    feed.title = pf_feed.get('title', '')[:MAX_FEEDNAME_LEN]
    feed.subtitle = pf_feed.get('subtitle', '')[:MAX_FEEDNAME_LEN]
    feed.link = pf_feed.get('link', '')[:MAX_URL_LEN]

    feed.http_etag = pf.get('etag')
    feed.http_modified = pf.get('modified')

    feed.last_update = make_datetime(pf.get('updated_parsed'))
    feed.json = json_dumps(pf_feed)
    db.add(feed)

    for e in pf.get('entries', ()):
        if not e:
            continue
        entry = None
        new_entry = False

        guid = e.get('id', e.get('link', '') + '@' + e.get('published', ''))
        if not guid:
            LOG.error("update_feed: can't generate a ID for entry %r of feed %r",
                      e, feed)
            continue

        entry = db.query(Entry).filter_by(feed=feed, guid=guid[:MAX_URL_LEN]).first()
        if not entry:
            entry = Entry(feed=feed)
            new_entry = True
        entry.guid = guid[:MAX_URL_LEN]
        entry.link = e.get('link', '')[:MAX_URL_LEN]
        entry.title = e.get('title', '')[:MAX_ENTRYTITLE_LEN]
        entry.published = make_datetime(e.get('published_parsed', entry.published))
        entry.updated = make_datetime(e.get('updated_parsed', entry.published))
        entry.retrieved_at = now()
        entry.json = json_dumps(e)
        db.add(entry)

        if new_entry:
# TODO: this should be replaced with INSERT INTO ... SELECT ... statement
            for subscription in db.query(Subscription).filter_by(feed=feed):
                db.add(Unread(entry=entry, user=subscription.user))

        existing_content = entry.content
        existing_hashes = set([c.hash for c in existing_content])
        actual_hashes = set()
        for c in e.get('content', ()):
            content = parse_content(c, entry=entry)
            actual_hashes.add(content.hash)
            if content.hash in existing_hashes:
                continue
            existing_hashes.add(content.hash)
            db.add(content)
        if 'summary_detail' in e:
            summary = parse_content(e.summary_detail, entry=entry, summary=True)
            actual_hashes.add(summary.hash)
            if summary.hash not in existing_hashes:
                db.add(summary)
        for old_content in existing_content:
            if old_content.hash not in actual_hashes:
                old_content.expired = True
                db.add(old_content)
    return feed

# vi: sw=4:ts=4:et
