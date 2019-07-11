/**
 * Processes marks and sends beacons to GA based on mark value
 * @param {Object} perfData - Object containing performance mark/measure information
 */
function handlePerfMarks(perfData) {
    if (!perfData.measureName) {
        // if there is no `measureName` property, just set a mark
        window.mdn.perf.setMark(perfData.markName);
    } else {
        window.mdn.perf.setMark(perfData.markName);
        window.mdn.perf.setMeasure({
            measureName: perfData.measureName,
            startMark: perfData.startMark,
            endMark: perfData.endMark
        });

        /* If Analytics has loaded, go ahead with tracking
           Checking for ".create" due to Ghostery mocking of ga.
           Use "window.ga" otherwise you'd get a
           "ReferenceError: ga is not defined" error. */
        if (window.ga && window.ga.create) {
            // Send event to GA
            window.ga('send', {
                hitType: 'timing',
                timingCategory: 'RUM - Interactive Examples',
                timingVar: perfData.measureName,
                timingValue:
                    window.mdn.perf.getDuration(perfData.measureName) || 0
            });
        }
    }
}

/**
 * Handles performance postMessages from the `head` of the
 * interactive examples iframe
 * @param {Object} event - The event Object associated with the postMessage
 */
function perfMsgHandler(event) {
    'use strict';

    var allowedOrigin =
        window.mdn.interactiveEditor.editorUrl ||
        'https://interactive-examples.mdn.mozilla.net';
    var eventData = event.data;

    if (event.origin !== allowedOrigin) {
        return false;
    }

    /* Only handle messages that came from the `head` of the
       interactive examples iframe */
    if (
        eventData.markName &&
        eventData.markName.indexOf('interactive-editor-') > -1
    ) {
        handlePerfMarks(eventData);
    }
}

/* Handles postMessages from the interactive editor. Specifically
   those that originates from the `head` of the iframe  */
window.addEventListener('message', perfMsgHandler, false);
