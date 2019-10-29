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
        const dummyGAFunc = jest.fn();
        window.ga = dummyGAFunc;

        create(
            <GAProvider>
                <Consumer>{contextConsumer}</Consumer>
            </GAProvider>
        );

        expect(dummyGAFunc).not.toHaveBeenCalled();
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

    test('hook works if there is a ga function', () => {
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

        function Test() {
            return GAProvider.useClientId();
        }

        const renderer = create(
            <GAProvider>
                <Test />
            </GAProvider>
        );
        expect(renderer.toJSON()).toBe('');
        act(() => {});
        expect(renderer.toJSON()).toBe('mockClientId');
    });
});
