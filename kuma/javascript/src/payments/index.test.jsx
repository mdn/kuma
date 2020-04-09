import React from 'react';
import { render, cleanup } from '@testing-library/react';
import PaymentsLandingPage from './index.jsx';
import UserProvider from '../user-provider.jsx';
import { title as signupTitle } from './subheaders/signup.jsx';
import { title as thankYouTitle } from './subheaders/thank-you.jsx';

const setup = (mockData = {}) => {
    const mockProps = {
        /* eslint-disable camelcase */
        data: { email: 'test@mozilla.com', next_subscriber_number: 99 },
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

    // Test the basics since more detailed tests are in each subheader
    test('it renders Signup subheader', () => {
        const { queryByText } = setup();
        expect(queryByText(signupTitle)).toBeTruthy();
    });

    test('it renders Thank You subheader if user is a subscriber', () => {
        const mockData = {
            isSubscriber: true,
        };
        const { queryByText } = setup(mockData);

        // Ensure that Thank You title renders
        expect(queryByText(thankYouTitle)).toBeTruthy();
    });

    test('it renders subscriber form', () => {
        const mockData = {
            waffle: {
                flags: {
                    ['subscription_form']: true,
                },

                // this is to avoid having to do a deep merge in setup()
                switches: {},
                samples: {},
            },
        };
        const { queryByTestId } = setup(mockData);
        expect(queryByTestId('subscription-form')).toBeTruthy();
    });
});
