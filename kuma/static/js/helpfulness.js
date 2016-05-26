(function(win, doc, $) {

    var waitBeforeAsking = 60000;
    var articleTracker = doc.location.pathname + '#answered-helpful';
    // this feature requires localStorage
    if (win.mdn.features.localStorage) {
        var ignore = localStorage.getItem('helpful-ignore') === 'true'; // true if ever clicked ignore
        var articleAskedRecently = parseInt(localStorage.getItem(articleTracker), 10) > Date.now();
        var helpfulnessAskedRecently = parseInt(localStorage.getItem('helpfulnessTracker'), 10) > Date.now();

        if (!ignore && !articleAskedRecently && !helpfulnessAskedRecently) {
            // ask about helpfulness after 1 min
            setTimeout(inquire, waitBeforeAsking);
        }
    }

    // create a notification
    function inquire() {
        // check we haven't asked on another page since we set timeout to trigger this
        var helpfulnessAskedRecently = parseInt(localStorage.getItem('helpfulnessTracker'), 10) > Date.now();
        if (helpfulnessAskedRecently) {
            return;
        }

        // dimension7 is "helpfulness"
        if(win.ga) ga('set', 'dimension7', 'Yes');

        // note that we have asked so we don't ask again for a while
        askAgainLater();

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
            confirm(gettext('Thanks for your feedback!'), 'success', 'Yes');
        });
        $('#helpful-no').on('click', function(e) {
            e.preventDefault();
            confirm('', 'error', 'No');
        });
        $('#helpful-ignore').on('click', function(e) {
            e.preventDefault();
            localStorage.setItem('helpful-ignore', 'true');
            confirm(gettext("We won't bug you again."), 'info', 'Ignore');
        });

        // create a dropdown in case the page is unhelpful
        var unhelpfulOptions = [
            {val: 'Translate', text: gettext('Translate it into my language')},
            {val: 'Make-Simpler', text: gettext('Make explanations clearer')},
            {val: 'Needs-More-Info', text: gettext('Add more details')},
            {val: 'Needs-Correction', text: gettext('Fix incorrect information')},
            {val: 'Needs-Examples', text: gettext('Add or improve examples')},
            {val: 'SEO', text: gettext('My search should have led to a different article')},
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
                mdn.analytics.trackEvent({
                    category: 'Helpful',
                    action: 'Clicked',
                    label: label
                });
                notification[type](msg, 2000);
            }
        }
    }

    // set a date for asking again
    function askAgainLater() {
        // ask about this particular article in 180 days
        localStorage.setItem(articleTracker, Date.now() + (1000*60*60*24)*180);
        // ask about any article in 7 days
        localStorage.setItem('helpfulnessTracker', Date.now() + (1000*60*60*24)*7);
    }

})(window, document, jQuery);
