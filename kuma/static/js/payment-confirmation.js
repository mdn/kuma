(function(win) {
    'use strict';

    // Fire analytic events only if the user has followed payment
    // flow denoted by `amountSubmitted` session varible.
    var sessionStoreKey = 'amountSubmitted';
    var amountSubmitted = sessionStorage.getItem(sessionStoreKey);
    var path = win.location.pathname;
    if (path.includes('/payments/success')) {
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

    } else if (path.includes('/payments/error')) {
        if (amountSubmitted) {
            mdn.analytics.trackError('Payment error', 'Payment failed');
        }
    }

})(window);
