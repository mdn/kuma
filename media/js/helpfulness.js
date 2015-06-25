(function(win, doc, $) {
    if (document.cookie.replace(/(?:(?:^|.*;\s*)helpful-stfu\s*\=\s*([^;]*).*$)|^.*$/, "$1") !== 'true') {
        if (window.waffle && window.waffle.flag_is_active('helpfulness')) {
             
            setTimeout(function() {
                var notification = mdn.Notifier.growl(gettext('Did this page help you?<br> <a href="#" class="notification-button" id="helpful-yes">Yes</a><a href="#" class="notification-button" id="helpful-no">No</a><a id="helpful-stfu" href="#">Never ask me again</a>'), { closable: true, duration: 0}).question();

                $('#helpful-yes').click(function() {
                   confirm("Thanks for your feedback!", 'success', 'Yes');
                });
                $('#helpful-no').click(function() {
                   confirm("", 'error', 'No');
                });
                $('#helpful-stfu').click(function() {
                   confirm("We won't bug you again.", 'info', 'STFU');
                   document.cookie = "helpful-stfu=true; expires=Fri, 31 Dec 9999 23:59:59 GMT;";
                });

                // create a dropdown in case the page is unhelpful 
                var unhelpful_options = [
                    {val: 'Translate', text: gettext('Translate it into my language')},
                    {val: 'Make-Simpler', text: gettext('Make it less confusing')},
                    {val: 'Needs-More-Info', text: gettext('It needs more information')},
                    {val: 'Incorrect', text: gettext('It contains incorrect information')},
                    {val: 'Other', text: gettext('Something else')}
                ]
                var $select = $('<select />').attr({
                    id: 'helpful-detail',
                    value: 'Choose one...'
                }).append($('<option>').attr('selected', 'selected').text('Choose one...'));
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
                        notification.error('Uh oh. What would make it better?<br>' + $select[0].outerHTML, 0);
                        $('#helpful-detail').change(function() {
                            confirm("Thanks! We\'ll fix it.", 'info', $(this).val());
                        });
                    }
                    else {
                        notification[type](gettext(msg), 2000);
                        mdn.analytics.trackEvent({
                            category: 'Helpful',
                            action: 'Clicked',
                            label: label
                        });
                    }
                }

            }, 60000);
        }
    }
})(window, document, jQuery);
