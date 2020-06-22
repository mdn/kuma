import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import Subscription, { successMsg } from './subscription.jsx';
import UserProvider from '../../user-provider.jsx';

const getProps = (userData = {}) => {
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...userData,
    };
    const mockResponse = {
        subscriptions: [
            {
                id: 'sub_H9PQHPTDQGQCK1',
                amount: 5,
                brand: 'Visa',
                expires_at: '11/2020', // eslint-disable-line camelcase
                last4: '4242',
                next_payment_at: '2020-05-23T08:04:40', // eslint-disable-line camelcase
                zip: '11201',
            },
        ],
    };

    return {
        contributionSupportEmail: 'mock-support@mozilla.com',
        locale: 'en-US',
        response: mockResponse,
        userData: mockUserData,
    };
};

describe('Subscription', () => {
    it('renders invitation if user is not subscriber', () => {
        const mockUserData = { isAuthenticated: true };
        const { userData } = getProps(mockUserData);

        render(
            <UserProvider.context.Provider value={userData}>
                <Subscription {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        expect(
            screen.getByText(/You have no active subscription/i)
        ).toBeInTheDocument();
    });

    it('renders subscriptions details for subscriber', async () => {
        const mockUserData = { isAuthenticated: true, isSubscriber: true };
        const { response, userData } = getProps(mockUserData);

        window.fetch = jest.fn(() =>
            Promise.resolve({ ok: true, json: () => response })
        );

        render(
            <UserProvider.context.Provider value={userData}>
                <Subscription {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        await waitFor(() => {
            expect(
                screen.queryByText(/You have no active subscription/i)
            ).not.toBeInTheDocument();
        });

        window.fetch.mockReset();
    });

    test('renders loading while fetching subscriptions data', async () => {
        const mockUserData = { isAuthenticated: true, isSubscriber: true };
        const mockResponse = {
            subscriptions: [],
        };
        const userData = getProps(mockUserData);

        window.fetch = jest.fn(() =>
            Promise.resolve({ ok: true, json: () => mockResponse })
        );

        render(
            <UserProvider.context.Provider value={userData}>
                <Subscription {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        await waitFor(() => {
            expect(screen.getByText(/loading/i)).toBeInTheDocument();
        });

        window.fetch.mockReset();
    });

    it('shows error message if cannot retrieve subscriptions', async () => {
        const mockUserData = { isAuthenticated: true, isSubscriber: true };
        const userData = getProps(mockUserData);

        // used by <GenericError />
        window.mdn = {
            contributionSupportEmail: 'mock-support@mozilla.com',
        };

        window.fetch = jest.fn(() => Promise.resolve({ ok: false }));

        render(
            <UserProvider.context.Provider value={userData}>
                <Subscription {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        await waitFor(() => {
            expect(
                screen.getByText(/sorry, something went wrong/i)
            ).toBeInTheDocument();
        });

        window.fetch.mockReset();
    });

    it('successfully cancels subscription', async () => {
        const mockUserData = { isAuthenticated: true, isSubscriber: true };
        const { response, userData } = getProps(mockUserData);

        let cancelConfirmButton = null;

        // mock first request to get subscriptions
        // second request is to cancel subscription
        window.fetch = jest
            .fn()
            .mockImplementationOnce(() =>
                Promise.resolve({ ok: true, json: () => response })
            )
            .mockImplementationOnce(() => Promise.resolve({ ok: true }));

        render(
            <UserProvider.context.Provider value={userData}>
                <Subscription {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        await waitFor(() => {
            const cancelButton = screen.getByRole('button', {
                name: /Cancel subscription/i,
            });

            expect(cancelButton).toBeInTheDocument();

            userEvent.click(cancelButton);

            cancelConfirmButton = screen.getByRole('button', {
                name: /Yes, cancel subscription/i,
            });

            expect(cancelConfirmButton).toBeInTheDocument();
        });

        userEvent.click(cancelConfirmButton);

        // Success message and no subscriptions message should show
        await waitFor(() => {
            expect(screen.getByText(successMsg)).toBeInTheDocument();
            expect(
                screen.getByText(/no active subscription/i)
            ).toBeInTheDocument();
        });

        window.fetch.mockReset();
    });

    test('clicking keep my membership button hides the cancel subscription form', async () => {
        const mockUserData = {
            isAuthenticated: true,
            isSubscriber: true,
        };
        const { response, userData } = getProps(mockUserData);

        let cancelButton = null;

        window.fetch = jest.fn(() =>
            Promise.resolve({ ok: true, json: () => response })
        );

        render(
            <UserProvider.context.Provider value={userData}>
                <Subscription {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        await waitFor(() => {
            cancelButton = screen.getByRole('button', {
                name: /Cancel subscription/i,
            });

            // cancel subscription button present
            expect(cancelButton).toBeInTheDocument();
        });

        userEvent.click(cancelButton);

        const cancellationForm = screen.getByRole('form', {
            name: /Are you sure you want to cancel?/i,
        });
        const keepSubscription = screen.getByRole('button', {
            name: /Keep subscription/i,
        });

        expect(cancellationForm).toBeVisible();

        userEvent.click(keepSubscription);

        expect(cancellationForm).not.toBeInTheDocument();

        window.fetch.mockReset();
    });
});
