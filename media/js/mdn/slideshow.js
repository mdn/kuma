/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/*****
/ jQuery tabbed slide show by Jenna Smith, http://www.growldesign.co.uk
/ Taken from (very long url follows):
/ http://net.tutsplus.com/tutorials/javascript-ajax/building-an-auto-scrolling-slideshow-that-works-with-and-without-javascript/
/
/ Additional Requirements:
/ 1. jQuery (http://jquery.com)
/ 2. Cycle plugin for jQuery (http://malsup.com/jquery/cycle/)
/*****/

$slideshow = {
    context: false,
    tabs: false,
    timeout: 7000,      // time before next slide appears (in ms)
    slideSpeed: 1000,   // time it takes to slide in each slide (in ms)
    tabSpeed: 100,      // time it takes to slide in each slide (in ms) when clicking through tabs
    fx: 'scrollLeft',         // the slide effect to use. See http://malsup.com/jquery/cycle/ for the list of effects

    init: function() {
        // set the context to help speed up selectors/improve performance
        this.context = $('#slideshow');

        // set tabs to current hard coded navigation items
        this.tabs = $('ol#slide-control li', this.context);

        // remove hard coded navigation items from DOM
        // because they aren't hooked up to jQuery cycle
        this.tabs.remove();

        // prepare slideshow and jQuery cycle tabs
        this.prepareSlideshow();
    },

    prepareSlideshow: function() {
        // initialise the jquery cycle plugin -
        // for information on the options set below go to:
        // http://malsup.com/jquery/cycle/options.html
        $('ol#slides', $slideshow.context).cycle({
            fx: $slideshow.fx,
            timeout: $slideshow.timeout,
            speed: $slideshow.slideSpeed,
            fastOnEvent: $slideshow.tabSpeed,
            pager: $('ol#slide-control', $slideshow.context),
            pagerAnchorBuilder: $slideshow.prepareTabs,
            before: $slideshow.activateTab,
            pauseOnPagerHover: true,
            pause: true
        });
    },

    prepareTabs: function(i, slide) {
        // return markup from hardcoded tabs for use as jQuery cycle tabs
        // (attaches necessary jQuery cycle events to tabs)
        return $slideshow.tabs.eq(i);
    },

    activateTab: function(currentSlide, nextSlide) {
        // get the active tab
        var activeTab = $('a[href="#' + nextSlide.id + '"]', $slideshow.context);

        // if there is an active tab
        if(activeTab.length) {
            // remove active styling from all other tabs
            $slideshow.tabs.removeClass('on');

            // add active styling to active button
            activeTab.parents('li').addClass('on');
        }
    }
};

$(function() {
    // add a 'js' class to the slideshow container.
    // We'll use this as a style hook so the content can degrade gracefully when JS is absent.
    var show = $("#slideshow");
    if(show.length) {
        show.addClass("js");
        // initialise the slideshow when the DOM is ready
        $slideshow.init();
    }
});
