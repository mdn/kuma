(function(win, doc, $) {

    // this feature requires localStorage
    if (('localStorage' in win)) {
        var ignore = localStorage.getItem('helpful-ignore') === 'true'; // true if ever clicked ignore
        var askedRecently = parseInt(localStorage.getItem(doc.location + '#answered-helpful'), 10) > Date.now();
        if (!ignore && !askedRecently) {
            // ask about helpfulness after 1 min
            setTimeout(inquire, 60000);
        }
    }

    // create a notification
    function inquire() {
        // dimension7 is "helpfulness"
        if(win.ga) ga('set', 'dimension7', 'Yes');

        // ask a simple question
        var ask = gettext('Did this page help you?') +
            '<br> <a href="#" class="notification-button" id="helpful-yes">' +
            gettext('Yes') +
            '</a><a href="#" class="notification-button" id="helpful-no">' +
            gettext('No') +
            '</a><a id="helpful-ignore" href="#">' +
            gettext('Never ask me again') +
            '</a>';
        var notification = mdn.Notifier.growl(ask, {closable: true, duration: 0}).question();

        // answers to the simple question include...
        $('#helpful-yes').on('click', function(e) {
            e.preventDefault();
            confirm('Thanks for your feedback!', 'success', 'Yes');
        });
        $('#helpful-no').on('click', function(e) {
            e.preventDefault();
            confirm('', 'error', 'No');
        });
        $('#helpful-ignore').on('click', function(e) {
            e.preventDefault();
            localStorage.setItem('helpful-ignore', 'true');
            confirm("We won't bug you again.", 'info', 'Ignore');
        });

        // create a dropdown in case the page is unhelpful
        var unhelpfulOptions = [
            {val: 'Translate', text: gettext('Translate it into my language')},
            {val: 'Make-Simpler', text: gettext('Make explanations clearer')},
            {val: 'Needs-More-Info', text: gettext('Add more details')},
            {val: 'Needs-Correction', text: gettext('Fix incorrect information')},
            {val: 'Other', text: gettext('Something else')}
        ]
        var $select = $('<select />').attr({
            id: 'helpful-detail'
        }).append($('<option>').attr('selected', 'selected').text(gettext('Choose one...')));
        $(unhelpfulOptions).each(function() {
            $select.append($('<option>').attr('value', this.val).text(this.text));
        });

        // handle feedback
        function confirm(msg, type, label) {
            // if "No" ask for more info
            if (type === 'error') {
                mdn.analytics.trackEvent({
                    category: 'Helpful',
                    action: 'Clicked',
                    label: label
                });
                notification.error(gettext('Uh oh. What would make it better?') + '<br>' + $select[0].outerHTML, 0);
                $('#helpful-detail').on('change', function(e) {
                    e.preventDefault();
                    confirm(gettext("Thanks! We'll fix it."), 'info', $(this).val());
                });
            }
            else {
                askAgainLater();
                mdn.analytics.trackEvent({
                    category: 'Helpful',
                    action: 'Clicked',
                    label: label
                });
                notification[type](gettext(msg), 2000);
            }
        }
    }

    // set a date (180 days ahead) for asking again
    function askAgainLater() {
        localStorage.setItem(doc.location + '#answered-helpful', Date.now() + (1000*60*60*24)*180);
    }

})(window, document, jQuery);
