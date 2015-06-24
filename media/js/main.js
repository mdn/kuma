(function(win, doc, $) {
    'use strict';

    /*
        Track clientside errors
    */
    mdn.analytics.trackClientErrors();

    /*
        Main menu
    */
    (function() {
        var $mainItems = $('#main-nav > ul > li');
        $mainItems.find('> a').mozMenu();
        $mainItems.find('.submenu').mozKeyboardNav();
    })();

    /*
        Search animation
    */

    (function() {
        var $nav = $('#main-nav');
        var $navItems = $nav.find('ul > li:not(.nav-search-link, .main-nav-search)');
        var $mainNavSearch = $nav.find('.main-nav-search');
        var $searchWrap = $nav.find('.search-wrap');
        var $input = $searchWrap.find('input');
        var $searchTrigger = $searchWrap.find('.search-trigger');
        var placeholder = $input.attr('placeholder');

        $searchTrigger.on('click', function(e) {
            $input.get(0).focus();
        });

        var timeout;
        var createExpander = function(isAdd) {
            return function(e) {

                if(isAdd) {
                    $input.select();
                }

                // If we're on mobile, just let everything be
                if($mainNavSearch.css('display') === 'block') {
                    return;
                }

                if(e) e.preventDefault();
                if(timeout) clearTimeout(timeout);
                timeout = setTimeout(function() {
                    if(isAdd) {
                        $navItems.fadeOut(100, function() {
                            $navItems.css('display', 'none');
                            $searchWrap.addClass('expanded');
                            $nav.addClass('expand');
                        });
                    }
                    else {
                        $nav.removeClass('expand');
                        timeout = setTimeout(function() {
                            $searchWrap.removeClass('expanded');
                            $navItems.fadeIn(400);
                        }, 250); // corresponds to length of CSS animation
                    }
                });
            };
        };

        $input.
            on('focus', createExpander(true)).
            on('blur', createExpander());
    })();

    /*
        Mobile search to display search box in menu
    */
    $('.nav-search-link a').on('click', function(e) {
        e.preventDefault();
        $('.main-nav-search').css('display', 'block').find('#main-q').get(0).focus();
        $('.nav-search-link').css('display', 'none');
    });


    /*
        Account for the footer language change dropdown and other dropdowns marked as autosubmit
    */
    $('select.autosubmit').on('change', function(){
        this.form.submit();
    });

    /*
        Disable forms when submitted
    */
    (function() {
        var disabled = 'disabled';

        $('form').on('submit', function(ev) {
            var $this = $(this);

            // Allow for a special CSS class to prevent this functionality
            if($this.hasClass('nodisable')) return;

            if ($this.data(disabled)) {
                ev.preventDefault();
            } else {
                $this.data(disabled, true).addClass(disabled);
            }

            $this.ajaxComplete(function(){
                $this.data(disabled, false).removeClass(disabled);
                $this.unbind('ajaxComplete');
            });
        });
    })();

    /*
        Send Django CSRF with all AJAX requests
    */
    $(doc).ajaxSend(function(event, xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (doc.cookie && doc.cookie !== '') {
                var cookies = doc.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        function sameOrigin(url) {
            // url could be relative or scheme relative or absolute
            var host = doc.location.host; // host + port
            var protocol = doc.location.protocol;
            var sr_origin = '//' + host;
            var origin = protocol + sr_origin;
            // Allow absolute or scheme relative URLs to same origin
            return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
                (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
                // or any other URL that isn't scheme relative or absolute i.e relative.
                !(/^(\/\/|http:|https:).*/.test(url));
        }
        function safeMethod(method) {
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
            xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        }
    });


    /*
        Skip to search and is better done with JS because it's sometimes hidden and shown
        Skip to main is also better done with JS as it is configurable on the server side
    */
    $('#skip-search').on('click', function(e) {
        e.preventDefault();
        $('input[name=q]').last().get(0).focus();
    });
    $('#skip-main').each(function() { // Only one, so using each as closure
        var id = this.href.split('#')[1];
        if(id) $('#' + id).attr('role', 'main');
    });

    /*
    Skip to select language doesn't work in fx without js
    */
    $('#skip-language').on('click', function(e) {
        e.preventDefault();
        $('#language').get(0).focus();
    });

    /*
        Create advanced and language menus
    */
    (function() {
        var $menus = $('#advanced-menu, #languages-menu');
        $menus.mozMenu();
        $menus.parent().find('.submenu').mozKeyboardNav();
    })();

    /*
        Messages / Notifications -- show the initial ones
    */
    (function() {
        // Find where we should put notifications
        var insertLocation;

        $.each([
            { selector: '#wikiArticle', method: 'prependTo' },
            { selector: '#home', method: 'prependTo' },
            { selector: 'h1', method: 'insertAfter' },
            { selector: 'body', method: 'prependTo' } // Default
        ], function() {
            if(!insertLocation && $(this.selector).length) {
                insertLocation = this;
            }
        });

        // Inject notifications
        $.each(mdn.notifications || [], function() {
            var encodedMessage = this.message;
            var messageHTML = $('<div />').html(encodedMessage).text();
            // Make it so
            $('<div />').attr({
                'class': 'notification ' + this.level + ' ' + this.tags,
                'data-level': this.level
            }).html(messageHTML)[insertLocation.method](insertLocation.selector);
        });

        // Make them official
        mdn.Notifier.discover();
    })();

})(window, document, jQuery);
