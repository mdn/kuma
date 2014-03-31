(function(doc, $) {
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
        $mainItems.find('> a').mozMenu({
            brickOnClick: function(e) { return e.target.tagName == 'I'; }
        });
        $mainItems.find('.submenu').mozKeyboardNav();
    })();

    /*
        Search animation
    */
    (function() {
        var $nav = $('#main-nav');
        var $navItems = $nav.find('ul > li:not(:last-child)');
        var $mainNavSearch = $nav.find('.main-nav-search');
        var $searchWrap = $nav.find('.search-wrap');
        var $input = $searchWrap.find('input');
        var $searchTrigger = $searchWrap.find('.search-trigger');
        var placeholder = $input.attr('placeholder');

        $searchTrigger.on('click', function(e) {
            $input.get(0).focus();
        });

        var timeout;
        var createExpander = function(delay, isAdd) {
            return function(e) {
                // If we're on mobile, just let everything be
                if($mainNavSearch.css('display') == 'block') {
                    return;
                }

                e && e.preventDefault();
                timeout && clearTimeout(timeout);
                timeout = setTimeout(function() {
                    if(isAdd) {
                        $navItems.fadeOut(100, function() {
                            $navItems.css('display', 'none');
                            $searchWrap.addClass('expanded');
                            $nav.addClass('expand');
                            setTimeout(function() {
                                $input.attr('placeholder', $input.attr('data-placeholder'));
                                $input.val($input.attr('data-value'));
                            }, 100);
                        });
                    }
                    else {
                        $nav.removeClass('expand');
                        $input.attr('placeholder', '');
                        $input.attr('data-value', $input.val());
                        $input.val('');
                        timeout = setTimeout(function() {
                            $searchWrap.removeClass('expanded');
                            $navItems.fadeIn(400);
                        } , 500);
                    }
                }, delay);
            };
        };

        $input.
            on('focus', createExpander(200, true)).
            on('blur', createExpander(600));
    })();

    /*
        Persona Login
    */
    (function() {
        var $loginButton = $('.persona-login');

        $loginButton.length && $.ajax({
            url: 'https://login.persona.org/include.js',
            dataType: 'script',
            cache: true,
            success: function() {
                $loginButton.addClass('persona-loaded').on('click', function(e) {
                    if(!$(this).hasClass('toggle')) {
                        navigator.id.get(function(assertion) {
                            if(!assertion) return;
                            $('input[name="assertion"]').val(assertion.toString());
                            $('form.browserid').first().submit();
                        });
                        return false;
                    }
                });
            }
        });
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
            if (doc.cookie && doc.cookie != '') {
                var cookies = doc.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
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
            return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
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
    */
    $('#skip-search').on('click', function(e) {
        e.preventDefault();
        $('input[name=q]').last().get(0).focus();
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

})(document, jQuery);
