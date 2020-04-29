import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import {
    toBeVisible,
    toBeInTheDocument,
} from '@testing-library/jest-dom/matchers';
import UserProvider from '../../user-provider.jsx';
import { title as cancelTitle } from '../components/cancel-subscription-form.jsx';
import { formatDate } from '../../formatters.js';
import ManagementPage, { title, successMsg } from './management.jsx';

expect.extend({ toBeVisible, toBeInTheDocument });

const setup = (userData = {}) => {
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...userData,
    };
    return render(
        <UserProvider.context.Provider value={mockUserData}>
            <ManagementPage locale="en-US" />
        </UserProvider.context.Provider>
    );
};

describe('Payments Management Page', () => {
    it('renders login view if user is not logged in', () => {
        window.mdn = {
            triggerAuthModal: jest.fn(),
        };
        const { getByText, queryByTestId } = setup();
        expect(getByText(title)).toBeInTheDocument();
        expect(queryByTestId('management-page')).toBeInTheDocument();

        // sign in link triggers auth modal
        const signInLink = getByText(/sign in/);
        expect(signInLink).toBeInTheDocument();
        fireEvent.click(signInLink);
        expect(window.mdn.triggerAuthModal).toHaveBeenCalled();
    });

    test('renders loading while fetching subscriptions data', async () => {
        const mockUserData = { isAuthenticated: true, isSubscriber: true };
        const mockResponse = {
            subscriptions: [],
        };

        window.fetch = jest.fn(() =>
            Promise.resolve({ ok: true, json: () => mockResponse })
        );

        const { getByText } = setup(mockUserData);
        await waitFor(() => {
            expect(getByText(/loading/i)).toBeInTheDocument();
            window.fetch.mockReset();
        });
    });

    it('shows no subscriptions message if not a subscriber', () => {
        const mockUserData = { isAuthenticated: true };
        const { getByText } = setup(mockUserData);
        expect(getByText(/no active subscriptions/i)).toBeInTheDocument();
    });

    it('shows error message if cannot retrieve subscriptions', async () => {
        const mockUserData = { isAuthenticated: true, isSubscriber: true };
        window.fetch = jest.fn(() => Promise.resolve({ ok: false }));
        window.mdn = {
            contributionSupportEmail: 'mock-support@mozilla.com',
        };
        const { getByText } = setup(mockUserData);
        await waitFor(() => {
            expect(
                getByText(/sorry, something went wrong/i)
            ).toBeInTheDocument();
            window.fetch.mockReset();
        });
    });

    test('subscriptions render and buttons work', async () => {
        const mockUserData = { isAuthenticated: true, isSubscriber: true };
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

        // mock first request to get subscriptions
        // second request is to delete subscription
        window.fetch = jest
            .fn()
            .mockImplementationOnce(() =>
                Promise.resolve({ ok: true, json: () => mockResponse })
            )
            .mockImplementationOnce(() => Promise.resolve({ ok: true }));

        const { getByText } = setup(mockUserData);
        const expected = mockResponse.subscriptions[0];

        // Content renders
        await waitFor(() => {
            // check last 4
            expect(
                getByText(expected.last4, { exact: false })
            ).toBeInTheDocument();

            // check expires at
            expect(getByText(expected.expires_at)).toBeInTheDocument();

            // check next payment date
            expect(
                getByText(formatDate('en-US', expected.next_payment_at), {
                    exact: false,
                })
            ).toBeInTheDocument();
        });

        // Click on cancel subscription button to show confirmation message
        let cancelBtn;
        await waitFor(() => {
            // there are two matches for `/cancel subscription/i`, so we use the
            // case-sensitive version to get the button:
            cancelBtn = getByText(/Cancel subscription/);
            expect(cancelBtn).toBeInTheDocument();
            fireEvent.click(cancelBtn);
            expect(getByText(cancelTitle)).toBeVisible();
        });

        // Click on Keep my membership button to hide confirmation message
        const keepBtn = getByText(/keep my membership/i);
        const cancelText = getByText(cancelTitle);
        fireEvent.click(keepBtn);

        expect(keepBtn).not.toBeInTheDocument();
        expect(cancelText).not.toBeInTheDocument();

        // Open confirmation again, click on "Yes, cancel subscription"
        fireEvent.click(cancelBtn);
        const submitBtn = getByText(/yes, cancel subscription/i);
        fireEvent.click(submitBtn);

        // Success message and no subscriptions message should show
        await waitFor(() => {
            expect(getByText(successMsg)).toBeInTheDocument();
            expect(getByText(/no active subscriptions/i)).toBeInTheDocument();
        });

        window.fetch.mockReset();
    });
});
