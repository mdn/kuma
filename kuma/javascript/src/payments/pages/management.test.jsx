import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import UserProvider from '../../user-provider.jsx';
import ManagementPage, { title } from './management.jsx';

const setup = (userData = {}) => {
    const mockData = { contributionSupportEmail: 'mock-support@mozilla.com' };
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...userData,
    };
    return render(
        <UserProvider.context.Provider value={mockUserData}>
            <ManagementPage locale="en-US" data={mockData} />
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
        expect(getByText(/no active subscription/i)).toBeInTheDocument();
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
});
