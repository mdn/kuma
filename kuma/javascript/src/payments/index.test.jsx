//@flow
import React from 'react';
import { render, cleanup } from '@testing-library/react';
import PaymentsLandingPage from './index.jsx';
import UserProvider from '../user-provider.jsx';
import { title, getSubtitle } from './thank-you-subheader.jsx';

const setup = (mockData = {}) => {
    const mockProps = {
        /* eslint-disable camelcase */
        data: { email: 'test@mozilla.com', next_subscriber_number: '99' },
        /* eslint-enable camelcase */
    };
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...mockData,
    };
    const utils = render(
        <UserProvider.context.Provider value={mockUserData}>
            <PaymentsLandingPage {...mockProps} />
        </UserProvider.context.Provider>
    );
    return utils;
};

describe('Payments Landing Page', () => {
    afterEach(() => {
        cleanup();
    });

    test('it renders promotional subheader', () => {
        const { queryByText } = setup();
        const mockSubscriberNumber = 99;

        expect(queryByText('Become a monthly supporter')).toBeTruthy();
        expect(
            queryByText(
                `You will be MDN member number: ${mockSubscriberNumber}`
            )
        ).toBeTruthy();
    });

    test('it renders Thank You subheader if user is a subscriber', () => {
        const subscriberNumber = 100;
        const mockData = {
            subscriberNumber,
            isSubscriber: true,
        };
        const expectedSubtitle = getSubtitle(subscriberNumber);
        const { queryByText } = setup(mockData);

        // Ensure that promo text is gone
        expect(queryByText('Become a monthly supporter')).toBeNull();

        // Ensure that Thank You content renders
        expect(queryByText(title)).toBeTruthy();
        expect(queryByText(expectedSubtitle)).toBeTruthy();
    });

    test('it renders subscriber form', () => {
        const mockData = {
            waffle: {
                flags: {
                    ['subscription_banner']: true,
                },

                // this is to avoid having to do a deep merge in setup()
                switches: {},
                samples: {},
            },
        };
        const { queryByTestId } = setup(mockData);
        expect(queryByTestId('payments-subscription-form')).toBeTruthy();
    });
});
