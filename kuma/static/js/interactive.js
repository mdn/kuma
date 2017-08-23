(function() {
    'use strict';

    var mediaQuery = window.matchMedia('(max-width: 1024px)');
    var iframe = document.querySelector('iframe.interactive');

    /**
     * A simple wrapper function for the `postMessage`s sent
     * to the interactive editor iframe
     * @param {Boolean} isSmallViewport - Boolean indicating whether to add, or
     * remove the `small-desktop-and-below` class
     */
    function postToEditor(isSmallViewport) {
        iframe.contentWindow.postMessage({ smallViewport: isSmallViewport },
            'https://interactive-examples.mdn.mozilla.net'
        );
    }

    /* As the user sizes the browser or tilts their device,
    listen for mediaQuery events and communicate the new
    viewport state to the interactive editor */
    mediaQuery.addListener(function(event) {
        if (event.matches) {
            postToEditor(true);
        } else {
            postToEditor(false);
        }
    });

    window.onload = function() {
        // if the mediaQuery matches on load
        if (mediaQuery.matches) {
            // add the class `small-desktop-and-below`
            postToEditor(true);
        }
    };

})();
