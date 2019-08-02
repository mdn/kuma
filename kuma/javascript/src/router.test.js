/* eslint-disable */
// ^ this is because of the disabling of client-side navigation is
// temporarily disabled.

// @flow
import React from 'react';
import { act, create } from 'react-test-renderer';

import Route from './route.js';
import Router from './router.jsx';

type TestRouteParams = { path: string };
type TestRouteData = { uppercase: string };
function TestComponent(props: { path: string, data: { uppercase: string } }) {
    return <div>{props.data.uppercase}</div>;
}

class TestRoute extends Route<TestRouteParams, TestRouteData> {
    getComponent() {
        return TestComponent;
    }
    match(url) {
        if (url.includes('test')) {
            return { path: url };
        } else {
            return null;
        }
    }

    fetch(params) {
        return Promise.resolve({ uppercase: params.path.toUpperCase() });
    }

    getTitle(params) {
        return 'fake title:' + params.path;
    }
}

// TODO: maybe I should just mock the perf.* methods here
// and write separate tests for perf.js
global.performance = {};
global.performance.clearMarks = jest.fn();
global.performance.clearMeasures = jest.fn();
global.performance.mark = jest.fn();
global.performance.measure = jest.fn();
global.performance.getEntriesByName = jest.fn(() => [{ duration: 100 }]);

window.scrollTo = jest.fn();
// $FlowFixMe
history.pushState = jest.fn();
// $FlowFixMe
document.body.addEventListener = jest.fn();

window.LUX = {
    init: jest.fn(),
    send: jest.fn()
};

// TODO: This is commented out in an effort to disable
// client-side navigation.
// See https://bugzilla.mozilla.org/show_bug.cgi?id=1570043
// This file, instead of deleting it, needs to have at least one
// test otherwise jest will complain. And if you'd just do an early
// return within the test, flow will complain.
test('Router', done => {
    return done();
});

// test('Router', done => {
//     jest.useFakeTimers();

//     // Render the router
//     const router = create(
//         <Router
//             routes={[new TestRoute()]}
//             initialURL="/test"
//             initialData={{ uppercase: '/TEST' }}
//         />
//     );

//     // Expect it to render a TestComponent
//     let component = router.root.findByType(TestComponent);
//     expect(component.props.path).toBe('/test');
//     expect(component.props.data.uppercase).toBe('/TEST');

//     // Expect the loading bar to be animating
//     let loadingBar = router.root.findAllByType('div')[0];
//     expect(loadingBar.props.className).toContain('loadingAnimation');

//     // Wait for effects to run
//     act(() => {});

//     // Expect the router to register intercepting event handlers
//     // $FlowFixMe
//     let mock = document.body.addEventListener.mock;
//     expect(mock.calls[0][0]).toBe('click');
//     expect(mock.calls[1][0]).toBe('submit');

//     // Remember the handlers so we can simulate clicks, etc.
//     let clickHandler = mock.calls[0][1];

//     // Run all timers, and expect the animation to have stopped
//     act(() => {
//         jest.runAllTimers();
//     });
//     expect(loadingBar.props.className).not.toContain('loadingAnimation');

//     let preventDefault = jest.fn();

//     // simulate a click on a link to a url we can not route to
//     // expect no client-side routing
//     act(() => {
//         const link = document.createElement('a');
//         link.href = '/foo/bar';
//         clickHandler({ button: 0, target: link, preventDefault });
//     });
//     expect(history.pushState.mock.calls.length).toBe(0);
//     expect(preventDefault).toHaveBeenCalledTimes(0);

//     // simulate a click on a link to a url we can route to but
//     // with a target attribute to open in a new tab
//     // expect no client-side routing
//     act(() => {
//         const link = document.createElement('a');
//         link.href = '/test/2';
//         link.target = '_blank';
//         clickHandler({ button: 0, target: link, preventDefault });
//     });
//     expect(history.pushState.mock.calls.length).toBe(0);
//     expect(preventDefault).toHaveBeenCalledTimes(0);

//     // simulate a click on a link to a url we can route to but
//     // not with the left mouse button
//     // expect no client-side routing
//     act(() => {
//         const link = document.createElement('a');
//         link.href = '/test/2';
//         clickHandler({ button: 1, target: link, preventDefault });
//     });
//     expect(history.pushState.mock.calls.length).toBe(0);
//     expect(preventDefault).toHaveBeenCalledTimes(0);

//     // simulate a click on a link to a url we can route to but
//     // with a modifier key held down
//     // expect no client-side routing
//     act(() => {
//         const link = document.createElement('a');
//         link.href = '/test/2';
//         clickHandler({
//             button: 0,
//             ctrlKey: true,
//             target: link,
//             preventDefault
//         });
//     });
//     expect(history.pushState.mock.calls.length).toBe(0);
//     expect(preventDefault).toHaveBeenCalledTimes(0);

//     // For all of the tests above, we should also be able to test
//     // that window.location is set to the link href for a regular
//     // page load, the window.locaiton mock that jest is using doesn't
//     // actually respond to sets.

//     // Expect the loading animation not to have been triggered
//     // by any of the simulated clicks above
//     expect(loadingBar.props.className).not.toContain('loadingAnimation');

//     // Expect neither of the LUX calls to have been called
//     expect(window.LUX.init.mock.calls.length).toBe(0);
//     expect(window.LUX.send.mock.calls.length).toBe(0);

//     // Now simulate a click on a link to a url we can route to
//     // and expect to see client side navigation
//     act(() => {
//         const link = document.createElement('a');
//         link.href = '/test/2';
//         clickHandler({ button: 0, target: link, preventDefault });
//     });

//     // Clicking on the link should cause a synchronous pushState call
//     // and we should also have called preventDefault on the event
//     expect(history.pushState.mock.calls[0][0]).toBe('/test/2');
//     expect(preventDefault).toHaveBeenCalledTimes(1);

//     // We should also have called LUX.init() but not send() at this point
//     expect(window.LUX.init.mock.calls.length).toBe(1);
//     expect(window.LUX.send.mock.calls.length).toBe(0);

//     // Expect the loading animation to have been triggered
//     expect(loadingBar.props.className).toContain('loadingAnimation');

//     // Wait a bit for asynchronous effects
//     process.nextTick(() => {
//         // Expect the document title to be set
//         expect(document.title).toBe('fake title:/test/2');

//         // Expect to have scrolled to the top
//         expect(window.scrollTo).toHaveBeenCalledTimes(1);

//         // Expect the component to have re-rendered
//         component = router.root.findByType(TestComponent);
//         expect(component.props.path).toBe('/test/2');
//         expect(component.props.data.uppercase).toBe('/TEST/2');

//         // Wait for effects to run after the render
//         act(() => {});

//         // And LUX.send() should have been called by now
//         expect(window.LUX.send.mock.calls.length).toBe(1);

//         done();
//     });
// });
