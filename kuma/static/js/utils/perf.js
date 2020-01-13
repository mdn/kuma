var mdn = window.mdn || {};

mdn.perf = {
    /**
     * Get and return the duration of the specified performance measure
     * @param {String} measureName - Name of the performance measure
     * @return {Number} the duration in milliseconds
     */
    getDuration: function(measureName) {
        'use strict';

        if (performance.getEntriesByName === undefined) {
            console.error(
                'performance.getEntriesByName is not supported by your user-agent'
            );
            return;
        }

        return performance.getEntriesByName(measureName)[0].duration;
    },
    setMark: function(label) {
        'use strict';

        if (performance.mark === undefined) {
            console.error(
                'performance.mark is not supported by your user-agent'
            );
            return;
        }

        /* Because a SyntaxError will be thrown if the provided label conflicts
           with a name that already exist in the PerformanceTiming interface,
           we wrap the call in a try/catch */
        try {
            performance.mark(label);
        } catch (error) {
            console.error('Error while setting performance mark: ', error);
        }
    },
    setMeasure: function(measureData) {
        'use strict';

        if (performance.measure === undefined) {
            console.error(
                'performance.measure is not supported by your user-agent'
            );
            return;
        }

        try {
            performance.measure(
                measureData.measureName,
                measureData.startMark,
                measureData.endMark
            );
        } catch (error) {
            console.error('Error while setting performance measure: ', error);
        }

    }
};
