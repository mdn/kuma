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
        // If we're using Speedcurve's LUX analytics, tell it that we're
        // starting a new client-side navigation
        try {
            if (
                typeof window === 'object' &&
                window.LUX &&
                typeof window.LUX.init === 'function'
            ) {
                window.LUX.init();
            }
        } catch (e) {
            console.error('LUX.init() error:', e);
        }
        // The LUX init call above also appears to clear everthing
        // But just to be sure we will explicitly clear the custom
        // marks and measures that we care about.
        performance.clearMarks(START);
        performance.clearMeasures(FETCH);
        performance.clearMeasures(RENDER);

        // Record the start time for a client-side navigation
        performance.mark(START);
    } catch (e) {
        console.error(e);
    }
}

export function navigateFetchComplete() {
    if (navigating) {
        try {
            // Record the time it takes to fetch page data during a
            // client-side navigation
            performance.measure(FETCH, START);
        } catch (e) {
            console.error(
                `Error in performance.measure(${JSON.stringify({
                    FETCH,
                    START
                })}) (error: ${e.toString()})`
            );
        }
    }
}

export function navigateRenderComplete(ga: GAFunction) {
    if (navigating) {
        navigating = false;

        try {
            // Record the time it takes to fetch page data and re-render
            // the page during client-side navigation
            performance.measure(RENDER, START);
        } catch (e) {
            console.error(
                `Error in performance.measure(${JSON.stringify({
                    FETCH,
                    START
                })}) (error: ${e.toString()})`
            );
        }

        // Send LUX data to Speedcurve to record the client-side navigation
        try {
            if (
                typeof window === 'object' &&
                window.LUX &&
                typeof window.LUX.send === 'function'
            ) {
                window.LUX.send();
            }
        } catch (e) {
            console.error('LUX.send() error:', e);
        }

        let fetchTime;
        let renderTime;
        try {
            fetchTime = performance.getEntriesByName(FETCH)[0].duration;
            renderTime = performance.getEntriesByName(RENDER)[0].duration;
        } catch (e) {
            console.error(
                `Error in performance.getEntriesByName() (${JSON.stringify({
                    FETCH,
                    RENDER
                })}) (error: ${e.toString()})`
            );
            return;
        }

        try {
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
            console.error(
                `Error sending to ga (${JSON.stringify({
                    fetchTime,
                    renderTime
                })}) (error: ${e.toString()})`
            );
        }
    }
}
