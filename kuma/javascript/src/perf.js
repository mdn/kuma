// @flow
// eslint-disable no-console
import type { GAFunction } from './ga-provider.jsx';

const START = 'client-side-navigate-start';
const FETCH = 'client-side-navigate-fetch';
const RENDER = 'client-side-navigate-render';

let navigating = false;

export function navigateStart() {
    navigating = true;
    try {
        performance.clearMarks(START);
        performance.clearMeasures(FETCH);
        performance.clearMeasures(RENDER);
        performance.mark(START);

        if (
            typeof window === 'object' &&
            window.LUX &&
            typeof window.LUX.init === 'function'
        ) {
            window.LUX.init();
        }
    } catch (e) {
        console.error(e);
    }
}

export function navigateFetchComplete() {
    if (navigating) {
        try {
            performance.measure(FETCH, START);
        } catch (e) {
            console.error(e);
        }
    }
}

export function navigateRenderComplete(ga: GAFunction) {
    if (navigating) {
        navigating = false;

        try {
            performance.measure(RENDER, START);

            if (
                typeof window === 'object' &&
                window.LUX &&
                typeof window.LUX.send === 'function'
            ) {
                window.LUX.send();
            }

            let fetchTime = performance.getEntriesByName(FETCH)[0].duration;
            let renderTime = performance.getEntriesByName(RENDER)[0].duration;

            ga('send', {
                hitType: 'timing',
                timingCategory: 'Client side navigation',
                timingVar: 'fetch',
                timingValue: Math.round(fetchTime)
            });

            ga('send', {
                hitType: 'timing',
                timingCategory: 'Client side navigation',
                timingVar: 'render',
                timingValue: Math.round(renderTime)
            });
        } catch (e) {
            console.error(e);
        }
    }
}
