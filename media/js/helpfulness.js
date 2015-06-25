(function(win, doc, $) {
    if (document.cookie.replace(/(?:(?:^|.*;\s*)helpful-stfu\s*\=\s*([^;]*).*$)|^.*$/, "$1") !== 'true') {
        if (window.waffle && window.waffle.flag_is_active('helpfulness')) {
            // if they stay a minute, ask if it was helpful
            setTimeout(function() {
                var question = mdn.Notifier.growl('Did this page help you?<br> <a href="#" class="notification-button" id="helpful-yes">Yes</a><a href="#" class="notification-button" id="helpful-no">No</a><a id="helpful-stfu" href="#">Never ask me again</a>', { closable: true, duration: 0}).question();

                $('#helpful-yes').click(function() {
                   confirm("Thanks for your feedback!", 'success', 'Yes');
                });
                $('#helpful-no').click(function() {
                   confirm("Thanks! We\'ll improve it.", 'error', 'No');
                });
                $('#helpful-stfu').click(function() {
                   confirm("We won't bug you again.", 'info', 'STFU');
                   document.cookie = "helpful-stfu=true; expires=Fri, 31 Dec 9999 23:59:59 GMT;";
                });

                function confirm(msg, type, label) {
                    question.close(question.item);
                    mdn.Notifier.growl(msg, { closable: true, duration: 2500 })[type]();
                    mdn.analytics.trackEvent({
                        category: 'Helpful',
                        action: 'Clicked',
                        label: label,
                        {'nonInteraction': 1} //http://www.lunametrics.com/blog/2014/05/06/noninteraction-events-google-analytics/
                    });
                }

            }, 60000);
        }
    }
})(window, document, jQuery);
