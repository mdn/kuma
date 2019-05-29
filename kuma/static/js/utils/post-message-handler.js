/**
 * Beacons events of type 'Performance Events' to GA
 * @param {Object} data - The data associated with this event
 */
function handlePerformanceEvents(data) {
    // one of hitType: event
    mdn.analytics.trackEvent({
        category: data.category,
        action: data.action,
        label:
            Math.random() // 5 random letters and digits
                .toString(36)
                .slice(-5) +
            '-' +
            new Date().getTime(),
        value: data.value - performance.timing.navigationStart
    });

    // one of hitType: timing
    mdn.analytics.trackTiming({
        category: data.category,
        timingVar: data.action,
        value: data.value - performance.timing.navigationStart
    });
}

/**
 * This sets a new mark, and a new measure. It then uses
 * this information to expose the total duration from
 * `navigationStart` of the parent document, until the
 * interactive example has reached `loadEventEnd`
 * @param {Object} perfData - Object containing performance mark/measure information
 */
function setLoadEventEnd(perfData) {
    var measureName = perfData.markName + '-measure';
    // set a mark
    window.mdn.perf.setMark(perfData.markName);
    /* Set a performance measure that is the duration from
       navigationStart until the interactive editor loaded */
    window.mdn.perf.setMeasure({
        measureName: measureName,
        startMark: 'navigationStart',
        endMark: perfData.markName
    });

    mdn.analytics.trackTiming({
        category: 'Interactive Examples',
        timingVar: measureName,
        value: window.mdn.perf.getDuration(measureName)
    });
}

window.mdn.postMessageHandler = {
    /**
     * Handles postMessages from the interactive editor, passing
     * the data in the relevant format to trackEvent depending on the label.
     * Also ensures that the origin of the message is what we expect.
     * @param {Object} event - The event Object received from the postMessage
     */
    interactiveExamplesMsgHandler: function(event) {
        'use strict';

        var allowedOrigin =
            window.mdn.interactiveEditor.editorUrl ||
            'https://interactive-examples.mdn.mozilla.net';
        var eventData = event.data;

        /* Do not handle messages if the message originated from an origin that is
           not the `allowedOrigin`, or came from the `head` of the interactive
           examples iframe */
        if (
            event.origin !== allowedOrigin ||
            (eventData.markName &&
                eventData.markName.indexOf('interactive-editor-') > -1)
        ) {
            return false;
        }

        if (eventData.label === 'Performance Events') {
            handlePerformanceEvents(eventData);
        } else if (
            eventData.markName &&
            eventData.markName.indexOf('ie-load-event-end') > -1
        ) {
            setLoadEventEnd(eventData);
        } else {
            mdn.analytics.trackEvent(eventData);
        }
    }
};

// handles postMessages from the interactive editor
window.addEventListener(
    'message',
    window.mdn.postMessageHandler.interactiveExamplesMsgHandler,
    false
);
