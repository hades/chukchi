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

UI = {
    source: null,
    unread: true
};

AllFeeds = {
    name: "All feeds",
    get: function(start, count, unread, callback) {
        Chukchi.getAllFeeds(start, count, unread, callback);
    }
};

function handleAuth(data) {
    $(".loading").remove();
    $(".screen").hide();
    if(data.state == 1) { // not logged in
        $(".login.screen").show();
        $(".login.screen .openid").focus();
        $(".login.screen form").submit(function(event) {
            event.preventDefault();
            Chukchi.login($(".login.screen .openid").val());
        });
        return;
    }
    if(data.state == 2) { // logged in
        $(".main.screen").show();
        setSource(AllFeeds);
        updateSubscriptions();
        return;
    }
}

function loadMoreEntries(count) {
    UI.scrollHandler = null;

    var start = UI.nextStartOffset;
    var token = UI.token;

    UI.source.get(start, count, UI.unread, function(total, entries) {
        if(token != UI.token)
            return;

        if(!entries) {
            console.log("no more entries");
            UI.scrollHandler = null;
            return;
        }

        $.each(entries, function(i, entry) {
            var $entry = makeEntryBlock(entry);
            $entry.appendTo($(".main.screen"));
            UI.nextStartOffset = entry.id;
        });

        updateSourceInfo(total);
        UI.scrollHandler = function(){ loadMoreEntries(10); };
        $(window).scroll();
    });
}

function makeEntryBlock(entry) {
    var $entry = $('.t .entry').clone();

    $entry.find('.feed').html(entry.feed.title);
    $entry.find('.title').html(entry.title);
    $entry.find('.date').html(entry.published);

    return $entry;
}

function makeFeedMenuItem(source) {
    if(typeof(source) == 'object') {
        var $item = $(".t .feedmenuselector").clone();
        $item.find('a').html(source.name);
        return $item;
    }
    var $item = $(".t .feedmenuseparator").clone();
    $item.html(source);
    return $item;
}

function makeFeedSource(subscription) {
    return {
        name: subscription.feed.title,
        get: function(start, count, unread, callback) {
            Chukchi.getEntries(subscription.feed, start, count, unread, callback);
        }
    };
}

function redrawEntries() {
    $(".page-header h1").hide();
    $(".page-header .loading").show();

    var token = (new Date).getTime();
    UI.token = token;

    UI.nextStartOffset = 0;
    loadMoreEntries(10);
}

function reportError(err) {
    // TODO: error reporting
}

function setSource(source) {
    UI.source = source;
    redrawEntries();
}

function updateSourceInfo(totalEntries) {
    $(".main.screen .loading").hide();
    var $header = $(".main.screen .page-header");

    $header.find('.source-name').html(UI.source.name);
    $header.find('small').html(totalEntries
                               + (UI.unread? ' new items' : ' items'));
    $header.find('h1').show();
}

function updateSubscriptions() {
    var $navlist = $("#navbar .nav-list");

    $navlist.find('li').remove();
    makeFeedMenuItem(AllFeeds).appendTo($navlist);
    makeFeedMenuItem("Feeds:").appendTo($navlist);

    Chukchi.getSubscriptions(function(subs) {
        $.each(subs, function(i, subscription) {
            makeFeedMenuItem(makeFeedSource(subscription)).appendTo($navlist);
        });
    });
}

$(document).ready(function(){
    Chukchi.apierror(reportError);
    Chukchi.auth(handleAuth);

    $(window).scroll(function(){
        if(!UI.scrollHandler)
            return;

        var windowHeight = $(window).height();
        var scrollTop = $(window).scrollTop();
        var bodyHeight = $(document).height();

        if( scrollTop + 200 > bodyHeight - windowHeight )
            UI.scrollHandler();
    });

    Chukchi.init();
});

}(window.jQuery);
// vim: sw=4:ts=4:et
