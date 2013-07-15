// Use a global k to share data accross JS files
k = {};

(function () {
    k.LAZY_DELAY = 500;  // delay to lazy loading scripts, in ms
    k.MEDIA_URL = '/media/';

    $(document).ready(function() {
        /* Focus form field when clicking on error message. */
        $('#content ul.errorlist a').click(function () {
                $($(this).attr('href')).focus();
                return false;
            });

        if ($('body').data('readonly') == 'true') {
            $forms = $('form[method=post]');
            $forms.find('input, button, select, textarea').attr('disabled', 'disabled');
            $forms.find('input[type=image]').css('opacity', .5);
        }

        initAutoSubmitSelects();
        disableFormsOnSubmit();
        lazyLoadScripts();
    });

    /*
     * Initialize some selects so that they auto-submit on change.
     */
    function initAutoSubmitSelects() {
        $('select.autosubmit').change(function() {
            $(this).closest('form').submit();
        });
    }

    /*
     * Disable forms on submit to avoid multiple POSTs when double+ clicking.
     * Adds `disabled` CSS class to the form for optionally styling elements.
     *
     * NOTE: We can't disable the buttons because it prevents their name/value
     * from being submitted and we depend on those in some views.
     */
    function disableFormsOnSubmit() {
        $('form').submit(function(ev) {
            var $this = $(this);

            // Allow for a special CSS class to prevent this functionality
            if($this.hasClass('nodisable')) return;

            if ($this.data('disabled')) {
                ev.preventDefault();
            } else {
                $this.data('disabled', true).addClass('disabled');
            }

            $this.ajaxComplete(function(){
                $this.data('disabled', false).removeClass('disabled');
                $this.unbind('ajaxComplete');
            });
        });
    }

    /*
     * This lazy loads our jQueryUI script.
     */
    function lazyLoadScripts() {
        var scripts = ['js/libs/jqueryui.min.js'],
            styles = [],  // was: ['css/jqueryui/jqueryui-min.css']
                          // turns out this messes with search
            i;

        // Don't lazy load scripts that have already been loaded
        $.each($('script'), function () {
            var this_src = $(this).attr('src');
            if (!this_src) return ;
            remove_item(scripts, this_src);
        });

        // Don't lazy load stylesheets that have already been loaded
        $.each($('link[rel="stylesheet"]'), function () {
            remove_item(styles, $(this).attr('href'));
        });

        setTimeout(function lazyLoad() {
            for (i in scripts) {
                $.get(k.MEDIA_URL + scripts[i]);
            }
            for (i in styles) {
                $('head').append(
                    '<link rel="stylesheet" type="text/css" href="' +
                    k.MEDIA_URL + styles[i] + '">');
            }
        }, k.LAZY_DELAY);
    }

    /*
     * Remove an item from a list if it matches the substring match_against.
     * Caution: modifies from_list.
     * E.g. list = ['string'], remove_item(list, 'str') => list is [].
     */
    function remove_item(from_list, match_against) {
        match_against = match_against.toLowerCase();
        for (var i in from_list) {
            if (match_against.indexOf(from_list[i]) >= 0) {
                from_list.splice(i, 1);
            }
        }
    }

})();


/**
 * Handles autofill of text with default value for browsers that don't
 * support the HTML5 `placeholder` functionality.
 *
 * When an input field is empty, the default value (from `placeholder`
 * attribute) will be set on blur. Then, when focused, the value will
 * be set to empty.
 *
 */
 $.fn.autoPlaceholderText = function () {

    // check for html5 placeholder support and fallback to js solution
    if (!('placeholder' in document.createElement('input'))) {

        function onFocus() {
            var $this = $(this);
            if ($this.val() === $this.attr('placeholder')) {
                $this.val('').addClass('placeholder-focused');
            }
        }

        function onBlur() {
            var $this = $(this);
            if ($this.val() === '') {
                $this.val($this.attr('placeholder')).removeClass('placeholder-focused');
            }
        }

        this.each(function () {
            var $this = $(this);
            var placeholder = $this.attr('placeholder');
            if (placeholder) {
                if (!$this.val() || $this.val() === placeholder) {
                    $this.val(placeholder).addClass('input-placeholder');
                }
                $this.focus(onFocus).blur(onBlur);
            }
        });

    }

    return this;
};

/*
 * Taken from Django's contrib/admin/media/js folder, thanks Django!
 * Copyright Django and licensed under BSD, please see django/LICENSE for
 * license details.
 * Modified slightly to handle fallback to full title if slug is empty.
 * Also modified to only trigger onchange.
 * Also modified to catch illegal slug characters
 */
$.fn.prepopulate = function(dependencies, maxLength) {
    /*
        Depends on urlify.js
        Populates a selected field with the values of the dependent fields,
        URLifies and shortens the string.
        dependencies - selected jQuery object of dependent fields
        maxLength - maximum length of the URLify'd string
    */

    return this.each(function() {
        var $field = $(this);

        $field.data("_changed", false);
        $field.change(function() {
            $field.data("_changed", true);
        });

        var populate = function () {
            // Bail if the fields value has changed
            if ($field.data("_changed") == true) return;

            var values = [], field_val, field_val_raw, split;
            dependencies.each(function() {
                if ($(this).val().length > 0) {
                    values.push($(this).val());
                }
            });

            s = values.join(" ");
            
            s = $.slugifyString(s);

            // Trim to first num_chars chars
            s = s.substring(0, maxLength);

            // Only replace the last piece (don't replace slug heirarchy)
            split = $field.val().split("/");
            split[split.length - 1] = s;
            $field.val(split.join("/"));
        };
        
        dependencies.keyup(populate).change(populate).focus(populate);
    });
};


// send django csrftoken with jquery ajax requests
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
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
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
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
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});
