//@flow
import React from 'react';
import { act, create } from 'react-test-renderer';

import UserProvider from './user-provider.jsx';

describe('UserProvider', () => {
    test('context works', () => {
        const P = UserProvider.context.Provider;
        const C = UserProvider.context.Consumer;
        const contextConsumer = jest.fn();
        const userData = {
            ...UserProvider.defaultUserData,
            username: 'testing'
        };

        create(
            <P value={userData}>
                <C>{contextConsumer}</C>
            </P>
        );

        // We expect that the consumer <C> will get the user data from
        // the provider <P> and pass it to the child function. This is
        // just verifying that we're using the React context API correctly.
        expect(contextConsumer.mock.calls.length).toBe(1);
        expect(contextConsumer.mock.calls[0][0]).toEqual(userData);
    });

    // This test passes but causes a warning message from
    // react-test-render about needing to make changes inside of an
    // act() call. Unfortunately, the change in question appears to be
    // the asyncronous resolution of the json promise, and I can't get
    // the warning to go away even with a really convoluted fetch()
    // mock. I think this is related to
    // https://github.com/facebook/react/issues/14769 and hopefully a
    // version of act() that can take async methods will fix the
    // issue.
    test('Provider fetches user data', done => {
        const P = UserProvider;
        const C = UserProvider.context.Consumer;
        const contextConsumer = jest.fn();
        const userData = {
            ...UserProvider.defaultUserData,
            username: 'testing',
            isStaff: true
        };

        // In this test we want to verify that UserProvider is
        // fetching user data from an API. So we need to mock fetch().
        global.fetch = jest.fn(() => {
            return Promise.resolve({
                json: () =>
                    Promise.resolve({
                        // We expect the server to send JSON data
                        // using snake_case
                        /* eslint-disable camelcase */
                        username: 'testing',
                        is_authenticated: false,
                        is_beta_tester: false,
                        is_staff: true,
                        is_super_user: false,
                        timezone: null,
                        gravatar_url: { small: null, large: null }
                        /* eslint-enable camelcase */
                    })
            });
        });

        act(() => {
            create(
                <P>
                    <C>{contextConsumer}</C>
                </P>
            );
        });

        // To start, we expect the contextConsumer function to be called
        // with the default null value. And we expect our fetch() mock to
        // be called when the component is first mounted, too.
        expect(contextConsumer).toHaveBeenCalledTimes(1);
        expect(contextConsumer).toHaveBeenCalledWith(null);
        expect(global.fetch).toHaveBeenCalledTimes(1);
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/whoami');

        // After the fetch succeeds, we expect contextConsumer to be
        // called again with the fetched userdata
        process.nextTick(() => {
            expect(contextConsumer).toHaveBeenCalledTimes(2);
            expect(contextConsumer.mock.calls[1][0]).toEqual(userData);
            done();
        });
    });
});
