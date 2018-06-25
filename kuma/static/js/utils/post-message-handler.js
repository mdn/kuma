/**
 * Beacons events of type 'Performance Events' to GA
 * @param {Object} data - The data associated with this event
 */
function handlePerformanceEvents(data) {
    // one of hitType: event
    mdn.analytics.trackEvent({
        category: data.category,
        action: data.action,
        label: new Date().getTime() + '-' + mdn.utils.randomString(5),
        value: data.value - performance.timing.fetchStart
    });

    // one of hitType: timing
    mdn.analytics.trackTiming({
        category: data.category,
        timingVar: data.action,
        value: data.value - performance.timing.fetchStart
    });
}

/**
 * Processes marks and sends beacons to GA based on mark value
 * @param {Object} perfData - Object containing performance mark/measure information
 */
function handlePerfMarks(perfData) {
    // if there is no `measureName` property, just set a mark
    if (!perfData.measureName) {
        window.mdn.perf.setMark(perfData.markName);
    } else {
        window.mdn.perf.setMark(perfData.markName);
        window.mdn.perf.setMeasure({
            measureName: perfData.measureName,
            startMark: perfData.startMark,
            endMark: perfData.endMark
        });

        mdn.analytics.trackTiming({
            category: 'RUM - Interactive Examples',
            timingVar: perfData.measureName,
            value: window.mdn.perf.getDuration(perfData.measureName)
        });
    }
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

        if (event.origin !== allowedOrigin) {
            return false;
        }

        console.info('====== eventData.label ======', eventData.label);

        if (eventData.label === 'Performance Events') {
            handlePerformanceEvents(eventData);
        } else if (eventData.markName) {
            handlePerfMarks(eventData);
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
