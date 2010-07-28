/*
 * questions.js
 * Scripts for the questions app.
 */

(function($){

    function init() {
        initSearch();

        if($('body').is('.new-question')) {
            initNewQuestion();
        }

        if($('body').is('.answers')) {
            initMoreDetailsModal();
            initReportPost();
            initHaveThisProblemTooAjax();
            initEmailSubscribeAjax();
        }
    }

    /*
     * Initialize the search widget
     */
    function initSearch() {
        // Setup the placeholder text
        $('#support-search input[name="q"]')
            // Setup the placeholder text
            .autoPlaceholderText()
            // Submit the form on Enter
            .keyup(function(ev) {
                if(ev.keyCode === 13 && $input.val()) {
                    $('#support-search form').submit();
                }
            });
    }

    /*
     * Initialize the new question page/form
     */
    function initNewQuestion() {
        var $questionForm = $('#question-form');
        prepopulateSystemInfo($questionForm);
        initTitleEdit($questionForm);
        hideDetails($questionForm);
    }

    // Autofill in the info we can get via js
    function prepopulateSystemInfo($form) {
        if($.browser.mozilla && isDesktopFF()) {
            $form.find('input[name="useragent"]').val(navigator.userAgent);
            $form.find('input[name="ff_version"]').val(getFirefoxVersion());
            $form.find('input[name="os"]').val(getOS());
            $form.find('textarea[name="plugins"]').val(getPlugins());
        }
    }

    // The title field become editable on click of the text or edit link
    function initTitleEdit($form) {
        $form.find('#title-val').click(function(ev){
            if($(ev.target).is('a, span')) {
                ev.preventDefault();
                var $this = $(this);
                var $hid = $this.find('input[type="hidden"]');
                var $textbox = $('<input type="text" name="' +
                               $hid.attr('name') + '" />');
                $textbox.val($hid.val());
                $this.unbind('click').replaceWith($textbox);
                $textbox.focus();
            }
        });
    }

    // Hide the browser/system details for users on FF with js enabled
    // and are submitting a question for FF on desktop.
    function hideDetails($form) {
        if($.browser.mozilla && isDesktopFF()) {
            $form.find('ol').addClass('hide-details');
            $form.find('a.show, a.hide').click(function(ev) {
                ev.preventDefault();
                $(this).closest('li')
                    .toggleClass('show')
                    .toggleClass('hide')
                    .closest('ol')
                        .toggleClass('show-details');
            });
        }

        if(!isDesktopFF()) {
            $form.find('li.system-details-info').hide();
        }
    }

    // Is the question for FF on the desktop?
    function isDesktopFF() {
        return document.location.search.indexOf('product=desktop') >= 0 ||
               document.location.search.indexOf('product=beta') >= 0;
    }

    // Returns a string with the version of Firefox
    function getFirefoxVersion() {
        var version = /Firefox\/(\S+)/i.exec(navigator.userAgent);
        if (version) {
            return version[1];
        } else {
            // Minefield pre-betas (nightlies)
            version = /Minefield\/(\S+)/i.exec(navigator.userAgent);
            if (version) {
                return version[1];
            }
        }

        return '';
    }

    // Returns a string representing the user's operating system
    function getOS() {
        var oscpu = navigator.oscpu;
        switch (oscpu) {
            case "Windows NT 5.1":
                return "Windows XP";
            case "Windows NT 6.0":
            case "Windows NT 6.0; WOW64":
                return "Windows Vista";
            case "Windows NT 6.1":
            case "Windows NT 6.1; WOW64":
                return "Windows 7";
            case "Linux i686":
                return "Linux";
            default:
                return oscpu;
        }
    }

    // Returns wiki markup for the list of plugins
    function getPlugins() {
        var plugins = [];
        for (var i = 0; i < navigator.plugins.length; i++) {
            var d = navigator.plugins[i].description.replace(/<[^>]+>/ig,'');
            if (plugins.indexOf(d) == -1) {
                plugins.push(d);
            }
        }
        if (plugins.length > 0) {
            plugins = "* " + plugins.join("\n* ");
        } else {
            plugins = "";
        }
        return plugins;
    }


    /*
     * Initialize the more details modal on answers page
     */
    function initMoreDetailsModal() {
        $('#show-more-details').click(function(ev){
            ev.preventDefault();

            var $modal = $(this).closest('div.side-section')
                                .find('div.more-system-details').clone();
            $modal.attr('id', 'more-system-details')
                  .append('<a href="#close" class="close">&#x2716;</a>');
            $modal.find('a.close').click(closeModal);

            var $overlay = $('<div id="modal-overlay"></div>');
            $overlay.click(closeModal);

            $('body').append($overlay).append($modal);

            function closeModal(ev) {
                ev.preventDefault();
                $modal.unbind().remove();
                $overlay.unbind().remove();
                delete $modal;
                delete $overlay;
                return false;
            }
        });
    }

    /*
     * Initialize the 'Report Post' form (ajaxify)
     */
    function initReportPost() {
        $('form.report input[type="submit"]').click(function(ev){
            ev.preventDefault();
            var $form = $(this).closest('form');
            if ($form.is('.processing')) {
                return false;
            }
            $('div.report-post-box').remove();

            var html = '<div class="report-post-box pop-in"><a href="#close" ' +
                       'class="close">&#x2716;</a><ul></ul></div>';
                $modal = $(html),
                $ul = $modal.find('ul');

            $form.find('select option').each(function(){
                var $this = $(this),
                    $li = $('<li><a href="#"></a></li>'),
                    $a = $li.find('a');
                $a.attr('data-val', $this.attr('value')).text($this.text());
                $ul.append($li);
            });
            $ul.append('<li><input type="text" class="text" ' +
                       'name="modal-other" /></li>');

            $modal.find('a.close').one('click', function(ev){
                ev.preventDefault();
                if ($form.is('.processing')) {
                    return false;
                }
                $modal.remove();
                return false;
            });

            $modal.find('ul a').click(function(ev){
                ev.preventDefault();
                if ($form.is('.processing')) {
                    return false;
                }
                $form.addClass('processing');

                $form.find('select').val($(this).attr('data-val'));
                var other = $modal.find('input[name="modal-other"]').val();
                $form.find('input[name="other"]').val(other);
                $.ajax({
                    url: $form.attr('action'),
                    type: 'POST',
                    data: $form.serialize(),
                    dataType: 'json',
                    success: function(data) {
                        $modal.find('ul').replaceWith('<div class="msg">' +
                                                    data.message + '</div>');
                    },
                    error: function() {
                        var message = gettext("There was an error :(.");
                        $modal.find('ul').replaceWith('<div class="msg">' +
                                                      message + '</div>');
                    },
                    complete: function() {
                        $form.removeClass('processing');
                    }
                });

                return false;
            });

            $form.append($modal);

            return false;
        });
    }

    /*
     * Ajaxify the "I have this problem too" form
     */
    function initHaveThisProblemTooAjax() {
        var $container = $('#question div.me-too');
        initAjaxForm($container, '#question-vote-thanks');
        $container.delegate('a.close, a.no-thanks', 'click', function(ev){
            ev.preventDefault();
            $container.unbind().remove();
            return false;
        });
    }

    /*
     * Ajaxify email subscribe
     */
    function initEmailSubscribeAjax() {
        var $container = $('#question ul.subscribe li.email'),
            $link = $('#email-subscribe-link');
        if ($link.length > 0) {
            $link.click(function(ev) {
                ev.preventDefault();
                $(this).closest('li').addClass('show-form');
                return false
            });
            initAjaxForm($container, '#email-subscribe');
            $container.delegate('a.close, a.no-thanks', 'click', function(ev){
                ev.preventDefault();
                $container.removeClass('show-form');
                return false;
            });
        }
    }

    // Helper
    function initAjaxForm($container, boxSelector) {
        $container.delegate('input[type="submit"]', 'click', function(ev){
            ev.preventDefault();
            var $form = $(this).closest('form');
            if ($form.is('.processing')) {
                return false;
            }
            $form.addClass('processing');
            $.ajax({
                url: $form.attr('action'),
                type: 'POST',
                data: $form.serialize(),
                dataType: 'json',
                success: function(data) {
                    if (data.html) {
                        $(boxSelector).remove();
                        $container.append(data.html);
                    } else if (data.message) {
                        var html = '<a class="close" href="#close">' +
                               '&#x2716;</a><div class="msg"></div>';
                        $(boxSelector)
                            .html(html)
                            .find('div.msg').text(data.message);
                    }
                },
                error: function() {
                    var message = gettext("There was an error :(.");
                    alert(message);
                },
                complete: function() {
                    $form.removeClass('processing');
                }
            });

            return false;
        });
    }

    $(document).ready(init);

}(jQuery));
