(function(win) {
    'use strict';

    // Fire analytic events only if the user has followed payment
    // flow denoted by `amountSubmitted` session varible.
    var amountSubmittedStoreKey = 'amountSubmitted';
    var amountSubmitted = sessionStorage.getItem(amountSubmittedStoreKey);
    var path = win.location.pathname;
    if (path.includes('/payments/success') && amountSubmitted) {
        mdn.analytics.trackEvent({
            category: 'payments',
            action: 'submission',
            label: 'completed',
            value: amountSubmitted
        }, function() {
            sessionStorage.removeItem(amountSubmittedStoreKey);
        });

    } else if (path.includes('/payments/error') && amountSubmitted) {
        mdn.analytics.trackEvent({
            category: 'Payment error',
            action: 'Payment failed'
        }, function() {
            sessionStorage.removeItem(amountSubmittedStoreKey);
        });
    }

})(window);
