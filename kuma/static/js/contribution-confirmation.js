(function(win) {
    'use strict';

    var path = win.location.pathname;
    if (path.includes('/contribute/success')) {
        // Only create one event per session to solve multiple events
        // being fired due to refreshing or reopening sessions
        var sessionStoreKey = 'hasSubmittedConfirmation';
        var hasSubmitted = sessionStorage.getItem(sessionStoreKey);

        if (hasSubmitted === null) {
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'submission',
                label: 'confirmation',
            }, function() {
                sessionStorage.setItem(sessionStoreKey, true);
            });
        }

    } else if (path.includes('/contribute/error')) {
        mdn.analytics.trackError('Payment error', 'Payment failed');
    }

})(window);
