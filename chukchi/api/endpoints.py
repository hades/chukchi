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

from functools import wraps

from flask import abort, g, redirect, request, session

from . import app, db, needs_session
from ..config import config
from ..db.models import Content, Entry, Feed, Subscription, Unread, User
from ..feed.discover import discover
from ..feed.opml import get_feed_urls

LOG = logging.getLogger(__name__)

MAX_ENTRY_COUNT = 500

@app.errorhandler(KeyError)
def no_key(e):
    return {'error': 400,
            'message': 'A field was missing from the request'}, 400

@app.route('/content/<int:content_id>', methods=('GET',))
@needs_session
def content(content_id):
    content = db.query(Content).filter_by(id=content_id).first()
    if not content:
        abort(404)
    result = content.to_json()
    result['data'] = content.data
    return result

def query_entries(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        start = int(request.args.get('start', 0))
        count = min(int(request.args.get('count', MAX_ENTRY_COUNT)), MAX_ENTRY_COUNT)
        unread = bool(request.args.get('unread', False))

        query = f(*args, **kwargs)
        if unread:
            query = query.join(Unread, (Entry.id == Unread.entry_id) &\
                                       (Unread.user_id == g.user.id))
        else:
            query = query.join(Subscription, (Entry.feed_id == Subscription.feed_id) &\
                                             (Subscription.user_id == g.user.id))
        query = query.order_by(Entry.id.desc())
        LOG.debug("query_entries f==%r unread==%s SQL: %s", f, unread, query.statement)
        total = query.count()
        if start:
            query = query.filter(Entry.id < start)
        query = query.limit(count)
        return {'total': total,
                'entries': [e.to_json() for e in query]}
    return wrapped

@app.route('/entries', methods=('GET',))
@needs_session
@query_entries
def get_all_entries():
    return db.query(Entry)

@app.route('/entries/<int:feed_id>', methods=('GET',))
@needs_session
@query_entries
def get_feed_entries(feed_id):
    return db.query(Entry).filter_by(feed_id=feed_id)

@app.route('/session', methods=('GET', 'DELETE'))
@needs_session
def get_delete_session():
    if request.method == 'DELETE':
        session.clear()
        return {}
    return {'user': g.user.id}

@app.route('/subscriptions', methods=('GET',))
@needs_session
def subscriptions():
    result = {'data': []}
    for s in g.user.subscriptions:
        sj = s.to_json()
        sj['unread_count'] = db.query(Entry)\
                               .filter_by(feed=s.feed)\
                               .join(Unread, (Entry.id == Unread.entry_id) &\
                                             (Unread.user_id == g.user.id))\
                               .count()
        result['data'].append(sj)
    return result

@app.route('/subscriptions', methods=('POST',))
@needs_session
def post_subscriptions():
    subscriptions_added = []
    errors = []
    urls = []
    if request.json:
        urls += request.json.get('urls', [])
    for file in request.files:
        try:
            for url in get_feed_urls(request.files[file].read()):
                urls.append(url)
        except Exception, e:
            LOG.exception("error parsing incoming file %s", file)
            errors.append({'file': file,
                           'error': unicode(e)})
    for s in urls:
        feed = discover(db, s)
        if not feed:
            LOG.error("no feed found at url %s", s)
            errors.append({'url': s,
                           'error': 'No feed found at the given url'})
            continue
        if db.query(Subscription)\
             .filter_by(user=g.user, feed=feed)\
             .first():
             errors.append({'url': s,
                            'error': 'You are already subscribed to this feed'})
             LOG.error("user %s is already subscribed to feed %s", g.user, s)
             continue
        db.add(Subscription(user=g.user, feed=feed))
        for t in db.query(Entry).filter_by(feed=feed)\
                   .order_by(Entry.id.desc())\
                   .limit(config.UNREAD_ENTRIES_IN_NEW_FEEDS):
            db.add(Unread(user=g.user, entry=t))
        subscriptions_added.append(feed.to_json())
    db.commit()
    if request.json:
        return {'subscriptions_added': subscriptions_added,
                'errors': errors}
    else:
        return redirect('/')

@app.route('/unread/<int:entry_id>', methods=('PUT', 'DELETE',))
@needs_session
def unread(entry_id):
    entry = db.query(Entry).filter_by(id=entry_id).first()
    if not entry:
        abort(404)
    unread_obj = db.query(Unread).filter_by(entry=entry, user=g.user).first()
    if request.method == 'PUT' and not unread_obj:
        db.add(Unread(entry=entry, user=g.user))
    elif request.method == 'DELETE' and unread_obj:
        db.delete(unread_obj)
    db.commit()
    return {}

@app.route('/unread/feed/<int:feed_id>', methods=('DELETE',))
@needs_session
def delete_unread_feed(feed_id):
    feed = db.query(Feed).filter_by(id=feed_id).first()
    if not feed:
        abort(404)
    req = db.query(Unread.id).filter_by(user=g.user)\
                             .join(Entry)\
                             .filter(Entry.feed == feed)
    req = db.query(Unread).filter(Unread.id.in_(req))
    req.delete(synchronize_session=False)
    db.commit()
    return {}

@app.route('/unread', methods=('DELETE',))
@needs_session
def delete_unread():
    req = db.query(Unread).filter_by(user=g.user)
    LOG.debug("delete_unread: SQL %s", str(req))
    req.delete()
    db.commit()
    return {}

# vi: sw=4:ts=4:et
