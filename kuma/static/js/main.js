(function(win, doc, $) {
    'use strict';

    /**
     * Track clientside errors
     */
    mdn.analytics.trackClientErrors();

    /**
     * Feature detection
     */
    win.mdn.features.localStorage = (function() {
        var uid = new Date;
        var result;
        try {
            localStorage.setItem(uid, uid);
            result = localStorage.getItem(uid) === uid.toString();
            localStorage.removeItem(uid);
            return result;
        } catch (exception) {
            return false;
        }
    }());

    /*
        Get URL Parameter
    */
    win.mdn.getUrlParameter = function(name) {
        name = name.replace(/[[]/, '\\[').replace(/[\]]/, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        var results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
    };

    /*
        Submenus
        - main and secondary navigation
        - language and admin menus
        - profile menu
    */

    (function() {
        var $submenus = $('.js-submenu');
        $submenus.prev('a, button').mozMenu();
        $submenus.mozKeyboardNav();
    })();

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
            if($this.hasClass('nodisable')) {
                return;
            }

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
        function sameOrigin(url) {
            // url could be relative or scheme relative or absolute
            var host = doc.location.host; // host + port
            var protocol = doc.location.protocol;
            var srOrigin = '//' + host;
            var origin = protocol + srOrigin;
            // Allow absolute or scheme relative URLs to same origin
            return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
                (url === srOrigin || url.slice(0, srOrigin.length + 1) === srOrigin + '/') ||
                // or any other URL that isn't scheme relative or absolute i.e relative.
                !(/^(\/\/|http:|https:).*/.test(url));
        }
        function safeMethod(method) {
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
            xhr.setRequestHeader('X-CSRFToken', mdn.utils.getCookie('csrftoken'));
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
        if(id) {
            $('#' + id).attr('role', 'main');
        }
    });

    /*
    Skip to select language doesn't work in fx without js
    */
    $('#skip-language').on('click', function(e) {
        e.preventDefault();
        $('#language').get(0).focus();
    });

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
