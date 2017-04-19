(function(Mozilla) {
    'use strict';

    var lou = new Mozilla.TrafficCop({
        id: 'experiment-framework-test',
        cookieExpires: 24 * 365, // 1 year
        variations: {
            'v=control': 50, // original
            'v=test': 50     // content from Experiment:FrameworkTest
        }
    });
    lou.init();

})(window.Mozilla);
