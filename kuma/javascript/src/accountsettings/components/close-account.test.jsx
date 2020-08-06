import * as React from 'react';
import { render, screen } from '@testing-library/react';

import CloseAccount from './close-account.jsx';
import UserProvider from '../../user-provider.jsx';

const getProps = (userData = {}) => {
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...userData,
    };

    return {
        locale: 'en-US',
        userData: mockUserData,
    };
};

describe('CloseAccount', () => {
    it('renders close account component', () => {
        const mockUserData = { isAuthenticated: true };
        const { userData } = getProps(mockUserData);

        render(
            <UserProvider.context.Provider value={userData}>
                <CloseAccount {...getProps(mockUserData)} />
            </UserProvider.context.Provider>
        );

        expect(
            screen.getByRole('region', { name: /Close Account/i })
        ).toBeInTheDocument();

        expect(
            screen.getByRole('link', { name: /Close account/i })
        ).toBeInTheDocument();
    });
});
