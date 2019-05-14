//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import LocaleProvider from './locale-provider.jsx';

describe('LocaleProvider', () => {
    test('provides the specified locale', () => {
        const Consumer = LocaleProvider.context.Consumer;
        const contextConsumer = jest.fn();

        create(
            <LocaleProvider locale="foo-bar">
                <Consumer>{contextConsumer}</Consumer>
            </LocaleProvider>
        );

        // We expect the Consumer to get the locale value from the provider
        // and pass it to the contextConsumer function.
        expect(contextConsumer.mock.calls.length).toBe(1);
        expect(contextConsumer.mock.calls[0][0]).toEqual('foo-bar');
    });
});
