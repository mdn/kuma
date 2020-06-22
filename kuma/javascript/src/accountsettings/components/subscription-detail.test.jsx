import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import SubscriptionDetail from './subscription-detail.jsx';
import UserProvider from '../../user-provider.jsx';

import { formatDate, formatMoney } from '../../formatters.js';

const getProps = (userData = {}) => {
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...userData,
    };
    const subscription = {
        id: 'sub_H9PQHPTDQGQCK1',
        amount: 5,
        brand: 'Visa',
        expires_at: '11/2020', // eslint-disable-line camelcase
        last4: '4242',
        next_payment_at: '2020-05-23T08:04:40', // eslint-disable-line camelcase
        zip: '11201',
    };

    return {
        contributionSupportEmail: 'mock-support@mozilla.com',
        locale: 'en-US',
        subscription,
        userData: mockUserData,
    };
};

describe('SubscriptionDetail', () => {
    test('subscription renders', () => {
        const mockUserData = {
            isAuthenticated: true,
            isSubscriber: true,
        };
        const { locale, subscription, userData } = getProps(mockUserData);
        const nextPaymentDate = formatDate(
            locale,
            subscription.next_payment_at
        );
        const amount = formatMoney(locale, subscription.amount / 100);

        render(
            <UserProvider.context.Provider value={userData}>
                <SubscriptionDetail {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        // next payment string
        expect(
            screen.getByText(
                `Next payment of ${amount} (monthly) occurs on ${nextPaymentDate}.`
            )
        ).toBeInTheDocument();

        // cancel subscription button present
        expect(
            screen.getByRole('button', { name: /Cancel subscription/i })
        ).toBeInTheDocument();

        // check brand and last 4
        expect(
            screen.getByText(
                `${subscription.brand} ending in ${subscription.last4}`
            )
        ).toBeInTheDocument();

        // check expires at
        expect(
            screen.getByText(`Expires ${subscription.expires_at}`)
        ).toBeInTheDocument();

        // check zip code
        expect(
            screen.getByText(`Postal/Zip Code: ${subscription.zip}`)
        ).toBeInTheDocument();

        // check subscription footer content
        expect(
            screen.getByText('To see your member perks', {
                exact: false,
            })
        ).toBeInTheDocument();

        expect(
            screen.getByText('If you have questions', {
                exact: false,
            })
        ).toBeInTheDocument();
    });

    test('clicking cancel button shows cancel subscription form', () => {
        const mockUserData = {
            isAuthenticated: true,
            isSubscriber: true,
        };
        const { userData } = getProps(mockUserData);

        render(
            <UserProvider.context.Provider value={userData}>
                <SubscriptionDetail {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        const cancelButton = screen.getByRole('button', {
            name: /Cancel subscription/i,
        });

        // cancel subscription button present
        expect(cancelButton).toBeInTheDocument();

        userEvent.click(cancelButton);
        expect(
            screen.getByRole('form', {
                name: /Are you sure you want to cancel?/i,
            })
        ).toBeVisible();
    });
});
