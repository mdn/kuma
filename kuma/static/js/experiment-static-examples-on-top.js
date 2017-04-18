(function() {
    'use strict';

    var lou = new Mozilla.TrafficCop({
        id: 'experiment-static-examples-on-top',
        cookieExpires: 24 * 365, // 1 year
        variations: {
            'v=control': 50, // original, archived ad Experiment:StaticExamplesOnTop
            'v=example': 50  // Static example at the top of the page, at "normal" location
        }
    });
    lou.init();

})(window.Mozilla);
