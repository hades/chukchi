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
    entries: [],
    selectedEntry: -1,
    source: null,
    unread: true
};

AllFeeds = {
    name: "All feeds",
    get: function(start, count, unread, callback) {
        Chukchi.getAllFeeds(start, count, unread, callback);
    },
    $menuitem: null
};

function handleAuth(data) {
    $(".loading").remove();
    $(".screen").hide();
    if(data.state == 1) { // not logged in
        $("#navbar").hide();
        $(".login.screen").show();
        $(".login.screen .openid").focus();
        $(".login.screen form").attr('action', Chukchi.loginUrl());
        return;
    }
    if(data.state == 2) { // logged in
        $("#navbar").show();
        $(".main.screen").show();
        updateSubscriptions();
        setSource(AllFeeds);
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

        updateSourceInfo(total);

        if(!entries) {
            console.log("no more entries");
            UI.scrollHandler = null;
            return;
        }

        $.each(entries, function(i, entry) {
            entry.unread = entry.unread || UI.unread;
            var $entry = makeEntryBlock(entry);
            $entry.appendTo($(".main.screen"));
            UI.nextStartOffset = entry.id;
            UI.entries.push($entry);
        });

        UI.scrollHandler = function(){ loadMoreEntries(10); };
        $(window).scroll();
    });
}

function makeEntryBlock(entry) {
    var $entry = $('.t .entry').clone();

    $entry.find('.feed').html(entry.feed.title);
    $entry.find('.title').html(entry.title);
    $entry.find('.date').html(moment(entry.published).fromNow());

    $entry.click(function(){
        selectEntry($entry);
    });

    if(entry.unread)
        $entry.addClass('unread');

    Chukchi.getContent(entry.content[0], function(content) {
        // TODO handle non-html, handle summary and expired content
        $entry.find('.text').html(content.data);
    });

    $entry.entry = entry;
    entry.$block = $entry;

    return $entry;
}

function makeFeedMenuItem(source) {
    if(typeof(source) == 'object') {
        var $item = $(".t .feedmenuselector").clone();
        $item.find('a').html(source.name);
        $item.click(function(){
            setSource(source);
        });
        if(source.unreadCount)
        {
            $("<span>").html(' (' + source.unreadCount + ')').appendTo($item.find('a'));
            $item.addClass('unread');
        }
        source.$menuitem = $item;
        return $item;
    }
    var $item = $(".t .feedmenuseparator").clone();
    $item.html(source);
    return $item;
}

function makeFeedSource(subscription) {
    return {
        name: subscription.feed.title,
        unreadCount: subscription.unread_count,
        get: function(start, count, unread, callback) {
            Chukchi.getEntries(subscription.feed, start, count, unread, callback);
        }
    };
}

function redrawEntries() {
    $(".page-header h1").hide();
    $(".page-header .loading").show();
    $(".main.screen .entry").remove();

    var token = (new Date).getTime();
    UI.token = token;
    UI.entries = [];
    UI.selectedEntry = -1;

    UI.nextStartOffset = 0;
    loadMoreEntries(10);
}

function reportError(err) {
    // TODO: error reporting
}

function selectEntry(entry) {
    var index = entry;
    if(typeof(entry) == 'object') {
        index = UI.entries.indexOf(entry);
    }

    $(".main.screen .entry.selected").removeClass('selected');

    if(UI.entries.length - index <= 3)
        loadMoreEntries(10);
    if(index < 0 || index >= UI.entries.length)
    {
        UI.selectedEntry = -1;
        return;
    }
    UI.selectedEntry = index;
    var $entry = UI.entries[index];
    $entry.addClass('selected');
    $('body').animate({
        scrollTop: $entry.offset().top
    }, 200);
    setUnread($entry.entry, false);
}

function setUnread(entry, flag) {
    if(flag == entry.unread)
        return;

    Chukchi.setUnread(entry, !!flag);
    entry.unread = !!flag;
    entry.unread? entry.$block.addClass('unread')
                : entry.$block.removeClass('unread');
}

function setSource(source) {
    UI.source = source;
    $("#navbar li.active").removeClass('active');
    if(source.$menuitem)
        source.$menuitem.addClass('active');
    redrawEntries();
}

function setupFeedAdder() {
    $("a.add-feed").click(function(event) {
        event.preventDefault();
        $(".feed-adder").show();
    });
    $(".feed-adder form").submit(function(event) {
        event.preventDefault();
        var url = $(this).find('input.url').val();
        if(url && url.length)
            Chukchi.addFeeds([url], function(){
                updateSubscriptions();
            });
    });
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

    setupFeedAdder();
    $(window).scroll(function() {
        if(!UI.scrollHandler)
            return;

        var windowHeight = $(window).height();
        var scrollTop = $(window).scrollTop();
        var bodyHeight = $(document).height();

        if( scrollTop + 200 > bodyHeight - windowHeight )
            UI.scrollHandler();
    });
    $(window).keypress(function(event) {
        if(event.which == 106) { // j
            event.preventDefault();
            selectEntry(UI.selectedEntry + 1);
            return;
        }
        if(event.which == 107) { // k
            event.preventDefault();
            selectEntry(UI.selectedEntry - 1);
            return;
        }
        if(event.which == 109) { // m
            event.preventDefault();
            var $entry = UI.entries[UI.selectedEntry];
            if($entry)
                setUnread($entry.entry, !$entry.entry.unread);
            return;
        }
        console.log("keypress: " + event.which);
    });

    Chukchi.init();
});

}(window.jQuery);
// vim: sw=4:ts=4:et
