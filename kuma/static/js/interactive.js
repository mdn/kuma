(function() {
    'use strict';

    var iframe = document.querySelector('iframe.interactive');
    var mediaQuery = window.matchMedia('(min-width: 63.9385em)');
    var targetOrigin =
        window.mdn.interactiveEditor.editorUrl ||
        'https://interactive-examples.mdn.mozilla.net';

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

                    // one of hitType: event
                    mdn.analytics.trackEvent({
                        category: 'Interactive Examples',
                        action: 'Time to iframe fetch start',
                        label:
                            new Date().getTime() +
                            '-' +
                            mdn.utils.randomString(5),
                        value: timeToIframeFetchStart
                    });

                    // one of hitType: timing
                    mdn.analytics.trackTiming({
                        category: 'Interactive Examples',
                        timingVar: 'Time to iframe fetch start',
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
})();
