(function(win) {
    'use strict';

    // Fire analytic events only if the user has followed payment
    // flow denoted by `amountSubmitted` session varible.
    var amountSubmittedStoreKey = 'submissionDetails';
    var submissionDetails = JSON.parse(sessionStorage.getItem(amountSubmittedStoreKey));

    // Default to no data
    var amountSubmitted = submissionDetails.amount || 0;
    var submissionPage = submissionDetails.page || '';

    var path = win.location.pathname;
    if (path.includes('/payments/success') && submissionDetails) {
        mdn.analytics.trackEvent({
            category: 'payments',
            action: 'success',
            label: submissionPage,
            value: amountSubmitted
        }, function() {
            sessionStorage.removeItem(amountSubmittedStoreKey);
        });

    } else if (path.includes('/payments/error') && submissionDetails) {
        mdn.analytics.trackEvent({
            category: 'Payment error',
            action: 'Payment failed'
        }, function() {
            sessionStorage.removeItem(amountSubmittedStoreKey);
        });
    }

})(window);
