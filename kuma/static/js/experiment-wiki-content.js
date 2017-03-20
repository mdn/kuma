(function() {
    'use strict';

    // cookie will expire in 24 hours
    var lou = new Mozilla.TrafficCop({
        id: 'experiment-wiki-content',
        // assumes all content experiments live at ?v=2
        variations: {
            'v=1': 50, // double control
            'v=2': 50 // variation w/new content
        }
    });

    // TODO: uncomment below to enable traffic redirection
    //lou.init();
})(window.Mozilla);
