// This file is part of Chukchi, the free web-based RSS aggregator
//
//   Copyright (C) 2013 Edward Toroshchin <chukchi-project@hades.name>
//
// Chukchi is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Chukchi is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// Please see the file COPYING in the root directory of this project.
// If you are unable to locate this file, see <http://www.gnu.org/licenses/>.

!function($){

var APIURL = 'http://127.0.0.1:5000/';

Chukchi = {};

Chukchi.authState = 0; // 0 — session check in progress
                       // 1 — unauthorized
                       // 2 — authorized
Chukchi.user = null;

Chukchi._hooks = {};

Chukchi._ajax = function(endpoint, options) {
    if(!options.error)
        options.error = function(jq) {
            Chukchi._runHooks('apierror', {jq: jq});
        }

    if(!options.contentType)
        options.contentType = 'application/json';

    if(options.data && typeof(options.data) == 'object'
                    && (['POST', 'PUT']).indexOf(options.method) >= 0
                    && options.contentType == 'application/json')
        options.data = JSON.stringify(options.data);

    $.ajax(APIURL + endpoint, options);
};

Chukchi._getSession = function() {
    Chukchi._ajax('session', {
        success: function(data) {
            Chukchi.user = data.user;
            Chukchi.authState = 2;
            Chukchi._runHooks('auth', {state: 2, user: data.user});
        },
        error: function(jq) {
            Chukchi.authState = 1;
            Chukchi._runHooks('auth', {state: 1});
        }
    });
};

Chukchi._makeHook = function(hookname) {
    this._hooks[hookname] = [];
    var hooker = function(callback) {
        this._hooks[hookname].push(callback);
    }
    this[hookname] = hooker;
};

Chukchi._runHooks = function(hookname, data) {
    $.each(this._hooks[hookname], function(i, hook) {
        try {
            hook(data);
        }
        catch(error) {
            console.log("error processing hook " + hookname + " " + hook + ": " + error);
        }
    });
};

Chukchi.addFeeds = function(feeds, callback) {
    this._ajax('subscriptions', {
        method: 'POST',
        data: {urls: feeds},
        success: callback
    });
};

Chukchi.deleteUnreadAll = function(callback) {
    this._ajax('unread', {
        method: 'DELETE',
        data: {},
        success: callback
    });
};

Chukchi.deleteUnreadFeed = function(feed, callback) {
    var id = feed;
    if(typeof(feed) == 'object')
        id = feed.id;
    this._ajax('unread/feed/' + id, {
        method: 'DELETE',
        data: {},
        success: callback
    });
};

Chukchi.getAllFeeds = function(start, count, unread, callback) {
    this._ajax('entries', {
        data: {start: start,
               count: count,
               unread: unread? 'unread': ''},
        success: function(result) {
            if(result.entries.length)
                callback(result.total, result.entries);
            else
                callback(result.total, false);
        }
    });
};

Chukchi.getContent = function(content, callback) {
    var id = content;
    if(typeof(content) == 'object')
        id = content.id;
    this._ajax('content/' + id, {
        success: function(result) {
            callback(result);
        }
    });
}

Chukchi.getEntries = function(feed, start, count, unread, callback) {
    var id = feed;
    if(typeof(feed) == 'object')
        id = feed.id;
    this._ajax('entries/' + id, {
        data: {start: start,
               count: count,
               unread: unread? 'unread': ''},
        success: function(result) {
            if(result.entries.length)
                callback(result.total, result.entries);
            else
                callback(result.total, false);
        }
    });
};

Chukchi.getSubscriptions = function(callback) {
    this._ajax('subscriptions', {
        success: function(result) {
            callback(result.data);
        }
    });
};

Chukchi.init = function() {
    this.apierror(function(data){
        console.log("api request failed: " + JSON.stringify(data));
    });

    this._getSession();
};

Chukchi.loginUrl = function() {
    return APIURL + 'openid/login';
};

Chukchi.postOpmlUrl = function() {
    return APIURL + 'subscriptions';
};

Chukchi.setUnread = function(entry, flag) {
    var id = entry;
    if(typeof(entry) == 'object')
        id = entry.id;
    this._ajax('unread/' + id, {
        method: flag? 'PUT' : 'DELETE',
    });
};

Chukchi._makeHook('apierror');
Chukchi._makeHook('auth');

}(window.jQuery);
// vim: sw=4:ts=4:et
