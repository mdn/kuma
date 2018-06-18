(function() {
    'use strict';

    var iframe = document.querySelector('iframe.interactive');
    var mediaQuery = window.matchMedia('(min-width: 63.9385em)');
    var targetOrigin =
        window.mdn.interactiveEditor.editorUrl ||
        'https://interactive-examples.mdn.mozilla.net';

    /**
     * Generate and returns a random string thanks to:
     * https://stackoverflow.com/questions/1349404/generate-random-string-characters-in-javascript
     */
    function randomString() {
        var text = '';
        var possible =
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

        for (var i = 0; i < 5; i++) {
            text += possible.charAt(
                Math.floor(Math.random() * possible.length)
            );
        }

        return text;
    }

    /**
     * Handles postMessages from the interactive editor, passing
     * the data in the relevant format to trackEvent depending on the label.
     * Also ensures that the origin of the message is what we expect.
     * @param {Object} event - The event Object received from the postMessage
     */
    function interactiveExamplesMsgHandler(event) {
        var allowedOrigin =
            window.mdn.interactiveEditor.editorUrl ||
            'https://interactive-examples.mdn.mozilla.net';

        if (event.origin !== allowedOrigin) {
            return false;
        }

        if (event.data.label === 'Performance Events') {
            mdn.analytics.trackEvent({
                category: event.data.category,
                action: event.data.action,
                label: new Date().getTime() + '-' + randomString(),
                value: event.data.value - performance.timing.fetchStart
            });
        } else {
            mdn.analytics.trackEvent(event.data);
        }
    }

    /**
     * Returns the interactive examples iframe performance entry
     * @param {Array} perfEntries - The array of performance entries
     */
    function getInteractiveExamplesPerfEntry(perfEntries) {
        for (var i = 0, l = perfEntries.length; i < l; i++) {
            var currentEntry = perfEntries[i];
            if (
                currentEntry.initiatorType &&
                currentEntry.initiatorType === 'iframe' &&
                currentEntry.name.indexOf(
                    'interactive-examples.mdn.mozilla.net'
                ) > -1
            ) {
                return perfEntries[i];
            }
        }
    }

    /* Ensure there is an iframe present and that performance is
       supported before gathering performance metric */
    if (iframe && performance !== undefined) {
        document.addEventListener('readystatechange', function(event) {
            if (event.target.readyState === 'complete') {
                var interactiveExamplesPerfEntry = {};
                var perfEntries = performance.getEntriesByType('resource');
                var mainFetchStart = 0;
                var iframeFetchStart = 0;
                var iframeFetchStartSinceUnixEpoch = 0;
                var timeToIframeFetchStart = 0;

                if (perfEntries === undefined || perfEntries.length <= 0) {
                    console.info('No performance entries was returned');
                    return;
                }

                interactiveExamplesPerfEntry = getInteractiveExamplesPerfEntry(
                    perfEntries
                );

                // ensure that the iframe was found in the array of performance entries
                if (interactiveExamplesPerfEntry !== undefined) {
                    mainFetchStart = performance.timing.fetchStart;
                    iframeFetchStart = Math.round(
                        interactiveExamplesPerfEntry.fetchStart
                    );
                    iframeFetchStartSinceUnixEpoch =
                        mainFetchStart + iframeFetchStart;

                    timeToIframeFetchStart =
                        new Date(iframeFetchStartSinceUnixEpoch) -
                        new Date(mainFetchStart);

                    mdn.analytics.trackEvent({
                        category: 'Interactive Examples',
                        action: 'Time to iframe fetch start',
                        label: new Date().getTime() + '-' + randomString(),
                        value: timeToIframeFetchStart
                    });
                }
            }
        });
    }

    /* If there is no `iframe`, or if this is a JS example,
    simply return */
    if (!iframe || iframe.classList.contains('interactive-js')) {
        return;
    }

    /**
     * A simple wrapper function for the `postMessage`s sent
     * to the interactive editor iframe
     * @param {Object} message - The message object sent to the interactive editor
     */
    function postToEditor(message) {
        iframe.contentWindow.postMessage(message, targetOrigin);
    }

    /* As the user sizes the browser or tilts their device,
    listen for mediaQuery events and communicate the new
    viewport state to the interactive editor */
    mediaQuery.addListener(function(event) {
        if (event.matches) {
            postToEditor({ smallViewport: false });
        } else {
            postToEditor({ smallViewport: true });
        }
    });

    window.onload = function() {
        // if the mediaQuery does not match on load
        if (!mediaQuery.matches) {
            // add the class `small-desktop-and-below`
            postToEditor({ smallViewport: true });
        }
    };

    // add event listener for postMessages from the interactive editor
    window.addEventListener('message', interactiveExamplesMsgHandler, false);
})();
