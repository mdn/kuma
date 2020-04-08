//@flow
/* eslint-disable camelcase */
import React from 'react';
import { act, create } from 'react-test-renderer';

import GAProvider from './ga-provider.jsx';
import UserProvider from './user-provider.jsx';

describe('UserProvider', () => {
    test('context works', () => {
        const P = UserProvider.context.Provider;
        const C = UserProvider.context.Consumer;
        const contextConsumer = jest.fn();
        const userData = {
            ...UserProvider.defaultUserData,
            username: 'testing',
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
    test('Provider fetches user data and waffle flags', (done) => {
        const P = UserProvider;
        const C = UserProvider.context.Consumer;
        const contextConsumer = jest.fn();

        const waffleFlags = {
            flags: { section_edit: true },
            switches: { bar: false },
            samples: {},
        };

        const userData = {
            ...UserProvider.defaultUserData,
            username: 'testing',
            isAuthenticated: true,
            isStaff: true,
            waffle: waffleFlags,
            email: 'testuser@mail.com',
        };

        // In this test we want to verify that UserProvider is
        // fetching user data from an API. So we need to mock fetch().
        global.fetch = jest.fn(() => {
            return Promise.resolve({
                json: () =>
                    Promise.resolve({
                        username: 'testing',
                        is_authenticated: true,
                        is_beta_tester: false,
                        is_staff: true,
                        is_super_user: false,
                        is_subscriber: false,
                        subscriber_number: null,
                        timezone: null,
                        avatar_url: null,
                        waffle: waffleFlags,
                        email: 'testuser@mail.com',
                    }),
            });
        });

        let gaMock = (window.ga = jest.fn());

        act(() => {
            create(
                <GAProvider>
                    <P>
                        <C>{contextConsumer}</C>
                    </P>
                </GAProvider>
            );
        });

        // To start, we expect the contextConsumer function to be called
        // with the default null value. And we expect our fetch() mock to
        // be called when the component is first mounted, too.
        // At this point we don't expect any GA calls
        expect(contextConsumer).toHaveBeenCalledTimes(1);
        expect(contextConsumer).toHaveBeenCalledWith(null);
        expect(global.fetch).toHaveBeenCalledTimes(1);
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/whoami');
        expect(gaMock).toHaveBeenCalledTimes(0);

        // After the fetch succeeds, we expect contextConsumer to be
        // called again with the fetched userdata. And we expect some
        // data to have been sent to the ga() function
        process.nextTick(() => {
            expect(contextConsumer).toHaveBeenCalledTimes(2);
            expect(contextConsumer.mock.calls[1][0]).toEqual(userData);
            expect(gaMock).toHaveBeenCalledTimes(4);
            expect(gaMock.mock.calls[0]).toEqual(['set', 'dimension1', 'Yes']);
            expect(gaMock.mock.calls[1]).toEqual(['set', 'dimension18', 'Yes']);
            expect(gaMock.mock.calls[2]).toEqual(['set', 'dimension9', 'Yes']);
            expect(gaMock.mock.calls[3][0]).toEqual('send');
            expect(gaMock.mock.calls[3][1].hitType).toEqual('pageview');
            done();
        });
    });
});
