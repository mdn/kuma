(function(win) {
    'use strict';

    var sessionStoreKey = 'amountSubmitted';
    var amountSubmitted = sessionStorage.getItem(sessionStoreKey);
    var path = win.location.pathname;
    if (path.includes('/contribute/success')) {
        // Only create one event per session to solve multiple events
        // being fired due to refreshing or reopening sessions

        if (amountSubmitted) {
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'submission',
                label: 'completed',
                value: amountSubmitted
            }, function() {
                sessionStorage.removeItem(sessionStoreKey);
            });
        }

    } else if (path.includes('/contribute/error')) {
        if (amountSubmitted) {
            mdn.analytics.trackError('Payment error', 'Payment failed');
        }
    }

})(window);
