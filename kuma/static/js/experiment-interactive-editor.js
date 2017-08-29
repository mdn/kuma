(function() {
    'use strict';

    var cop = new Mozilla.TrafficCop({
        id: 'experiment-interactive-editor',
        cookieExpires: 24 * 365, // 1 year
        variations: {
            'v=a': 50, // control
            'v=b': 50 // interactive editor
        }
    });

    cop.init();
})();
