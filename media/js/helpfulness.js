(function(win, doc, $) {
    // no localStorage, no helpfulness rating
    if (('localStorage' in win)) {
        var stfu = localStorage.getItem('helpful-stfu') === 'true'; // true if ever clicked stfu
        var asked_recently = parseInt(localStorage.getItem(doc.location + '#answered-helpful')) > Date.now();
        if (!stfu && !asked_recently) {

            setTimeout(function() {

                // create a notification with a simple question
                var ask = gettext('Did this page help you?') +
                    '<br> <a href="#" class="notification-button" id="helpful-yes">' +
                    gettext('Yes') +
                    '</a><a href="#" class="notification-button" id="helpful-no">' +
                    gettext('No') +
                    '</a><a id="helpful-stfu" href="#">' +
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
                $('#helpful-stfu').on('click', function(e) {
                    e.preventDefault();
                    localStorage.setItem('helpful-stfu', 'true');
                    confirm("We won't bug you again.", 'info', 'STFU');
                });

                // create a dropdown in case the page is unhelpful
                var unhelpful_options = [
                    {val: 'Translate', text: gettext('Translate it into my language')},
                    {val: 'Make-Simpler', text: gettext('Make it less confusing')},
                    {val: 'Needs-More-Info', text: gettext('Add more information')},
                    {val: 'Needs-Correction', text: gettext('Correct bad information')},
                    {val: 'Other', text: gettext('Something else')}
                ]
                var $select = $('<select />').attr({
                    id: 'helpful-detail'
                }).append($('<option>').attr('selected', 'selected').text(gettext('Choose one...')));
                $(unhelpful_options).each(function() {
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

                // set a date (180 days ahead) for asking again
                function askAgainLater() {
                    localStorage.setItem(doc.location + '#answered-helpful', Date.now() + (1000*60*60*24)*180);
                }
            }, 60000); // display inquiry after 1 minute
        }
    }
})(window, document, jQuery);
