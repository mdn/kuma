//@flow
import React from 'react';
import { act, create } from 'react-test-renderer';

import GAProvider from './ga-provider.jsx';

describe('GAProvider', () => {
    beforeEach(() => {
        delete window.ga;
    });

    test('Provides the window.ga() function', () => {
        const Consumer = GAProvider.context.Consumer;
        const contextConsumer = jest.fn();
        const dummyGAFunc = () => {};
        window.ga = dummyGAFunc;

        create(
            <GAProvider>
                <Consumer>{contextConsumer}</Consumer>
            </GAProvider>
        );

        // We expect GAProvider to set window.ga as its value and we
        // expect the Consumer to get that value from the provider and
        // pass it to the contextConsumer function.
        expect(contextConsumer.mock.calls.length).toBe(1);
        expect(contextConsumer.mock.calls[0][0]).toEqual(dummyGAFunc);
    });

    test('Provides a dummy if no window.ga function', () => {
        const Consumer = GAProvider.context.Consumer;
        const contextConsumer = jest.fn();

        create(
            <GAProvider>
                <Consumer>{contextConsumer}</Consumer>
            </GAProvider>
        );

        // If there is no window.ga() function defined, we expect
        // GAProvider to provide a dummy function anyway.
        expect(window.ga).toBe(undefined);
        expect(contextConsumer.mock.calls.length).toBe(1);
        expect(typeof contextConsumer.mock.calls[0][0]).toBe('function');
    });
});

// Test our custom clientId hook
describe('GAProvider.useClientId', () => {
    beforeEach(() => {
        delete window.ga;
    });

    test('hook returns "" if there is no ga function', () => {
        function Test() {
            const clientId = GAProvider.useClientId();
            expect(clientId).toBe('');
            return null;
        }

        create(
            <GAProvider>
                <Test />
            </GAProvider>
        );
    });

    test('hook works if there is a ga function', done => {
        const mockTrackerObject = {
            get(p) {
                return p === 'clientId' ? 'mockClientId' : '';
            }
        };

        function mockGA(f) {
            act(() => {
                f(mockTrackerObject);
            });
        }
        window.ga = mockGA;

        let numCalls = 0;

        function Test() {
            const clientId = GAProvider.useClientId();
            switch (numCalls) {
                case 0:
                    expect(clientId).toBe('');
                    numCalls++;
                    break;
                case 1:
                    expect(clientId).toBe('mockClientId');
                    done();
            }
            return null;
        }

        create(
            <GAProvider>
                <Test />
            </GAProvider>
        );
        act(() => {});
    });
});
