import React from 'react';
import { render, screen } from '@testing-library/react';

import AccountSettingsLandingPage from './index.jsx';
import UserProvider from '../../user-provider.jsx';

const getTestData = (mockData = {}) => {
    const mockProps = {
        /* eslint-disable camelcase */
        data: { email: 'test@mozilla.com', next_subscriber_number: 99 },
        /* eslint-enable camelcase */
    };
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...mockData,
    };
    return {
        mockProps,
        mockUserData,
    };
};

describe('Account Settings Landing Page', () => {
    it('renders the account settings form for authenticated users', () => {
        const mockData = getTestData({
            isAuthenticated: true,
        });

        render(
            <UserProvider.context.Provider value={mockData.mockUserData}>
                <AccountSettingsLandingPage {...mockData.mockProps} />
            </UserProvider.context.Provider>
        );

        expect(screen.queryByTestId('user-details-form')).toBeTruthy();
        expect(screen.queryByText('Sign in')).not.toBeInTheDocument();
    });

    it('show singin link for unauthticated users', () => {
        const mockData = getTestData();

        render(
            <UserProvider.context.Provider value={mockData.mockUserData}>
                <AccountSettingsLandingPage {...mockData.mockProps} />
            </UserProvider.context.Provider>
        );

        expect(screen.getByText('Sign in')).not.toBeNull();
        expect(screen.queryByTestId('user-details-form')).toBeNull();
    });
});
